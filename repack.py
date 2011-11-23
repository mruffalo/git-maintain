#!/usr/bin/env python
import argparse
from subprocess import Popen, PIPE

git_command = ('git', '--git-dir={}')
count_objects = git_command + ('count-objects',)
repack = git_command + ('repack', '-Ad')

p = argparse.ArgumentParser()
p.add_argument('git_dir_path', nargs='+')
args = p.parse_args()

for git_dir_path in args.git_dir_path:
    s = Popen((x.format(git_dir_path) for x in count_objects), stdout=PIPE)
    s.wait()
    output = s.stdout.read()
    print(repr(output))
    object_count = int(output.split()[0])
    print(object_count)
