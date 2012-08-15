#!/usr/bin/env python
from __future__ import print_function
from argparse import ArgumentParser
from fnmatch import fnmatch
from os import listdir, walk
from os.path import abspath, split as osps, join as ospj, isdir
from subprocess import Popen, PIPE

git_command = ('git', '--git-dir={0}')
count_objects = git_command + ('count-objects',)
repack = git_command + ('repack', '-Ad')
prune = git_command + ('prune', '-v')
pack_refs = git_command + ('pack-refs',)
pack_pattern = '*.pack'
git_dir_pattern = '.git'

def find_git_dirs(path):
    for dirpath, dirnames, _ in walk(path):
        for dirname in dirnames:
            if git_dir_pattern in dirname:
                yield ospj(dirpath, dirname)

def get_pack_count(path):
    pack_dir = ospj(path, 'objects', 'pack')
    if isdir(pack_dir):
        packs = [p for p in listdir(pack_dir) if fnmatch(p, pack_pattern)]
        return len(packs)
    else:
        return 0

def should_repack(git_dir_path):
    Popen((x.format(git_dir_path) for x in pack_refs)).wait()
    s = Popen((x.format(git_dir_path) for x in count_objects), stdout=PIPE)
    s.wait()
    output = s.stdout.read()
    object_count = int(output.split()[0])
    dir_name_pieces = osps(git_dir_path)
    if dir_name_pieces[1] == '.git':
        display_name = dir_name_pieces[0]
    else:
        display_name = git_dir_path
    pack_count = get_pack_count(git_dir_path)
    print('{0}: {1} loose objects, {2} pack(s)'.format(display_name,
                                                       object_count, pack_count))
    return object_count or (pack_count - 1)

if __name__  == '__main__':
    p = ArgumentParser()
    p.add_argument('directory')
    p.add_argument('-n', '--pretend', action='store_true')
    args = p.parse_args()
    for git_directory in find_git_dirs(args.directory):
        if should_repack(git_directory) and not args.pretend:
            Popen((x.format(git_directory) for x in repack)).wait()
            Popen((x.format(git_directory) for x in prune)).wait()

