import os
import shutil
import subprocess
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import click


def check_output(cmd: list[str], dry_run: bool = True, cwd: Optional[str] = None) -> Optional[str]:
    if dry_run:
        click.echo(
            click.style("Dry run; not running.", fg="red") + " Would run: {}".format(" ".join(cmd))
        )
        return None
    else:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, cwd=cwd)


def which_(exe: str) -> Optional[str]:
    """Uses shutil to look for an executable, mimicking unix which."""
    # Replaced distutils.spawn with shutil.which for Python 3.12+ compatibility
    return shutil.which(exe)


def all_equal(iterable: Iterable[object]) -> bool:
    return len(set(iterable)) == 1


def discover_git_root(path: Path) -> Path:
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    raise ValueError("Could not find git root")


@contextmanager
def pushd(path: Path) -> Iterator[None]:
    original_dir = Path.cwd()
    os.chdir(path)
    yield
    os.chdir(original_dir)


def git_ls_files(pattern: str) -> list[str]:
    return (
        subprocess.run(["git", "ls-files", pattern], check=True, text=True, capture_output=True)
        .stdout.strip()
        .split("\n")
    )


def get_all_repo_packages() -> list[Path]:
    git_root = discover_git_root(Path(__file__))
    with pushd(git_root):
        return [
            Path(p).parent
            for p in subprocess.run(
                ["git", "ls-files", "**/setup.py"], check=True, text=True, capture_output=True
            )
            .stdout.strip()
            .split("\n")
        ]
