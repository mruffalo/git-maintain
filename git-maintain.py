#!/usr/bin/env python3
from argparse import ArgumentParser
from fnmatch import fnmatch
from os import listdir
from os.path import abspath, split as osps, join as ospj, isdir
from pathlib import Path
from shutil import rmtree
from subprocess import Popen, PIPE

try:
    from scandir import walk
except ImportError:
    from os import walk

git_command = ('git', '--git-dir={}')
count_objects = git_command + ('count-objects',)
repack = git_command + ('repack', '-Ad')
prune = git_command + ('prune', '-v')
pack_refs = git_command + ('pack-refs', '--all')
# TODO don't hardcode 'origin'
remote_prune = git_command + ('remote', 'prune', 'origin')
pack_pattern = '*.pack'
git_dir_pattern = '.git'

def find_git_dirs(path: Path):
    for dirpath_str, dirnames, _ in walk(str(path)):
        dirpath = Path(dirpath_str)
        for dirname in dirnames:
            if dirname.endswith(git_dir_pattern):
                yield dirpath / dirname

def get_pack_count(path: Path):
    pack_dir = path / 'objects' / 'pack'
    if pack_dir.is_dir():
        packs = [p for p in pack_dir.iterdir() if p.match(pack_pattern)]
        return len(packs)
    else:
        return 0

def should_repack(git_dir_path: Path):
    command = [
        piece.format(git_dir_path)
        for piece in pack_refs
    ]
    Popen(command).wait()

    command = [
        piece.format(git_dir_path)
        for piece in count_objects
    ]
    s = Popen(command, stdout=PIPE)
    s.wait()
    output = s.stdout.read()
    object_count = int(output.split()[0])

    if git_dir_path.name == '.git':
        display_name = git_dir_path.parent / git_dir_path.stem
    else:
        display_name = git_dir_path

    pack_count = get_pack_count(git_dir_path)
    print(
        '{}: {} loose objects, {} pack(s)'.format(
            display_name,
            object_count,
            pack_count,
        )
    )
    return object_count or (pack_count - 1)

def remove_logs(git_dir_path: Path):
    git_log_dir = git_dir_path / 'logs'
    if git_log_dir.is_dir():
        rmtree(str(git_log_dir))

if __name__  == '__main__':
    p = ArgumentParser()
    p.add_argument('directory', type=Path)
    p.add_argument('--remote-prune', action='store_true')
    p.add_argument('--remove-logs', action='store_true')
    p.add_argument('-n', '--pretend', action='store_true')
    args = p.parse_args()
    for git_directory in find_git_dirs(args.directory):
        if args.remote_prune:
            Popen((x.format(git_directory) for x in remote_prune)).wait()
        if args.remove_logs:
            remove_logs(git_directory)
        force_repack = False
        if args.remote_prune or args.remove_logs:
            force_repack = True
            print('{0}: repack forced'.format(git_directory))
        if (force_repack or should_repack(git_directory)) and not args.pretend:
            Popen((x.format(git_directory) for x in repack)).wait()
            Popen((x.format(git_directory) for x in prune)).wait()

