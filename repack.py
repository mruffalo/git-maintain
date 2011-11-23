#!/usr/bin/env python
import argparse
from os.path import split as osps
from subprocess import Popen, PIPE

git_command = ('git', '--git-dir={}')
count_objects = git_command + ('count-objects',)
repack = git_command + ('repack', '-Ad')
prune = git_command + ('prune', '-v')
pack_refs = git_command + ('pack-refs',)

p = argparse.ArgumentParser()
p.add_argument('git_dir_path', nargs='+')
p.add_argument('--pretend', action='store_true')
args = p.parse_args()

for git_dir_path in args.git_dir_path:
    Popen((x.format(git_dir_path) for x in pack_refs)).wait()
    s = Popen((x.format(git_dir_path) for x in count_objects), stdout=PIPE)
    s.wait()
    output = s.stdout.read()
    object_count = int(output.split()[0])
    print('{}: {} loose objects'.format(osps(git_dir_path)[0], object_count))
    if object_count and not args.pretend:
        Popen((x.format(git_dir_path) for x in repack)).wait()
        Popen((x.format(git_dir_path) for x in prune)).wait()
