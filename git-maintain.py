#!/usr/bin/env python3
from argparse import ArgumentParser
from os import walk
from pathlib import Path
from shutil import rmtree
from subprocess import Popen, PIPE, check_call, run
from typing import Iterable, Sequence

REPOSITORY_COLOR = '\033[01;34m'
NO_COLOR = '\033[00m'

GIT = 'git'
PACK_PATTERN = '*.pack'
GIT_DIR_OR_FILE_PATTERN = '.git'

def colorize_repo_name(repo_name) -> str:
    return f'{REPOSITORY_COLOR}{repo_name}{NO_COLOR}'

class GitCommandRunner:
    def __init__(self, git_dir: Path, pretend: bool):
        self.git_dir = git_dir
        self.pretend = pretend

        if self.git_dir.name == '.git':
            self.display_name = git_dir.parent / git_dir.stem
        else:
            self.display_name = git_dir

    def __call__(self, *args: Sequence[str], **subprocess_kwargs):
        command = [GIT, *args]
        command_str = ' '.join(command)
        if not self.pretend:
            return run(command, check=True, **subprocess_kwargs)

    def print(self, *args, **kwargs):
        args = [f'{colorize_repo_name(self.git_dir)}:'] + list(args)
        print(*args, **kwargs)

    def get_pack_count(self) -> int:
        pack_dir = self.git_dir / 'objects/pack'
        if pack_dir.is_dir():
            packs = list(pack_dir.glob(PACK_PATTERN))
            return len(packs)
        else:
            return 0

    def should_repack(self) -> bool:
        proc = self('count-objects', stdout=PIPE)
        output = proc.stdout.decode()
        object_count = int(output.split()[0])

        pack_count = self.get_pack_count()
        self.print(f'{object_count} loose objects, {pack_count} pack(s)')
        return bool(object_count or (pack_count > 1))

    def delete_log_dir(self):
        git_log_dir = self.git_dir / 'logs'
        if git_log_dir.is_dir():
            rmtree(git_log_dir)

def read_relative_git_dir(git_submodule_file: Path) -> Path:
    with open(git_submodule_file) as f:
        pieces = next(f).strip().split()
        if pieces[0] == 'gitdir:':
            # Not sure whether anything else would ever be present,
            # but be safe just in case
            return Path(pieces[1])

def find_git_dirs(path: Path) -> Iterable[Path]:
    resolved = path.resolve()
    for dirpath_str, dirnames, filenames in walk(path):
        dirpath = Path(dirpath_str)
        for dirname in dirnames:
            if dirname.endswith(GIT_DIR_OR_FILE_PATTERN):
                yield dirpath / dirname
        if GIT_DIR_OR_FILE_PATTERN in filenames:
            relative_repo_path = read_relative_git_dir(dirpath / GIT_DIR_OR_FILE_PATTERN)
            yield (dirpath / relative_repo_path).resolve().relative_to(resolved)

def delete_log_dir(git_dir_path: Path):
    git_log_dir = git_dir_path / 'logs'
    if git_log_dir.is_dir():
        rmtree(git_log_dir)

def maintain_repository(git_directory: Path, remote_prune: bool, remove_logs: bool, pretend: bool):
    git = GitCommandRunner(git_directory, pretend)
    git('pack-refs', '--all')

    if remote_prune:
        # TODO don't hardcode 'origin'
        git('remote', 'prune', 'origin')
    if remove_logs:
        delete_log_dir(git_directory)
    force_repack = False
    if remote_prune or remove_logs:
        force_repack = True
        git.print('repack forced')
    if (force_repack or git.should_repack()) and not pretend:
        git('repack', '-Ad')
        git('prune', '-v')

if __name__  == '__main__':
    p = ArgumentParser()
    p.add_argument('directory', type=Path, nargs='?', default=Path())
    p.add_argument('--remote-prune', action='store_true')
    p.add_argument('--remove-logs', action='store_true')
    p.add_argument('-n', '--pretend', action='store_true')
    args = p.parse_args()

    for git_directory in find_git_dirs(args.directory):
        maintain_repository(git_directory, args.remote_prune, args.remove_logs, args.pretend)
