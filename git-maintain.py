#!/usr/bin/env python3
from argparse import ArgumentParser
from os import walk
from pathlib import Path
from shutil import rmtree
from subprocess import Popen, PIPE, check_call
from typing import Iterable


REPOSITORY_COLOR = '\033[01;34m'
NO_COLOR = '\033[00m'

git_command = ('git', '--git-dir={}')
count_objects = git_command + ('count-objects',)
repack = git_command + ('repack', '-Ad')
prune = git_command + ('prune', '-v')
pack_refs = git_command + ('pack-refs', '--all')
# TODO don't hardcode 'origin'
remote_prune_command = git_command + ('remote', 'prune', 'origin')
pack_pattern = '*.pack'
git_dir_pattern = '.git'

def find_git_dirs(path: Path) -> Iterable[Path]:
    for dirpath_str, dirnames, _ in walk(path):
        dirpath = Path(dirpath_str)
        for dirname in dirnames:
            if dirname.endswith(git_dir_pattern):
                yield dirpath / dirname

def get_pack_count(path: Path) -> int:
    pack_dir = path / 'objects/pack'
    if pack_dir.is_dir():
        packs = list(pack_dir.glob(pack_pattern))
        return len(packs)
    else:
        return 0

def colorize_repo_name(repo_name) -> str:
    return f'{REPOSITORY_COLOR}{repo_name}{NO_COLOR}'

def should_repack(git_dir_path: Path) -> bool:
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
    print(f'{colorize_repo_name(display_name)}: {object_count} loose objects, {pack_count} pack(s)')
    return bool(object_count or (pack_count > 1))

def delete_log_dir(git_dir_path: Path):
    git_log_dir = git_dir_path / 'logs'
    if git_log_dir.is_dir():
        rmtree(git_log_dir)

def maintain_repository(git_directory: Path, remote_prune: bool, remove_logs: bool, pretend: bool):
    if remote_prune:
        check_call([x.format(git_directory) for x in remote_prune_command])
    if remove_logs:
        delete_log_dir(git_directory)
    force_repack = False
    if remote_prune or remove_logs:
        force_repack = True
        print(f'{colorize_repo_name(git_directory)}: repack forced')
    if (force_repack or should_repack(git_directory)) and not pretend:
        check_call([x.format(git_directory) for x in repack])
        check_call([x.format(git_directory) for x in prune])

if __name__  == '__main__':
    p = ArgumentParser()
    p.add_argument('directory', type=Path)
    p.add_argument('--remote-prune', action='store_true')
    p.add_argument('--remove-logs', action='store_true')
    p.add_argument('-n', '--pretend', action='store_true')
    args = p.parse_args()

    for git_directory in find_git_dirs(args.directory):
        maintain_repository(git_directory, args.remote_prune, args.remove_logs, args.pretend)
