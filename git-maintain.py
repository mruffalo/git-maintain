#!/usr/bin/env python
from __future__ import print_function
import argparse
from fnmatch import fnmatch
from os import listdir
from os.path import split as osps, join as ospj, isdir
from subprocess import Popen, PIPE

git_command = ('git', '--git-dir={0}')
count_objects = git_command + ('count-objects',)
repack = git_command + ('repack', '-Ad')
prune = git_command + ('prune', '-v')
pack_refs = git_command + ('pack-refs',)
pack_pattern = '*.pack'

p = argparse.ArgumentParser()
p.add_argument('git_dir_path', nargs='+')
p.add_argument('--pretend', action='store_true')
args = p.parse_args()

def get_pack_count(path):
    pack_dir = ospj(path, 'objects', 'pack')
    if isdir(pack_dir):
        packs = [p for p in listdir(pack_dir) if fnmatch(p, pack_pattern)]
        return len(packs)
    else:
        return 0

for git_dir_path in args.git_dir_path:
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
    if (object_count or (pack_count - 1)) and not args.pretend:
        Popen((x.format(git_dir_path) for x in repack)).wait()
        Popen((x.format(git_dir_path) for x in prune)).wait()
