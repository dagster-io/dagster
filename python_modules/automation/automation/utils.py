import os
import subprocess
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from distutils import spawn
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
    """Uses distutils to look for an executable, mimicking unix which."""
    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


def all_equal(iterable: Iterable[object]) -> bool:
    return len(set(iterable)) == 1


def discover_oss_root(path: Path) -> Path:
    while path != path.parent:
        if (path / ".git").exists() or path.name == "dagster-oss":
            return path
        path = path.parent
    raise ValueError("Could not find OSS root")


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


def _pyproject_toml_is_package(path: str) -> bool:
    """Check if a pyproject.toml file defines a Python package (has a [project] section)."""
    with open(path) as f:
        content = f.read()
    return "\n[project]" in content or content.startswith("[project]")


def get_all_repo_packages() -> list[Path]:
    oss_root = discover_oss_root(Path(__file__))
    with pushd(oss_root):
        setup_paths = (
            subprocess.run(
                ["git", "ls-files", "python_modules/**/setup.py"],
                check=True,
                text=True,
                capture_output=True,
            )
            .stdout.strip()
            .split("\n")
        )
        pyproject_paths = (
            subprocess.run(
                ["git", "ls-files", "python_modules/**/pyproject.toml"],
                check=True,
                text=True,
                capture_output=True,
            )
            .stdout.strip()
            .split("\n")
        )
        package_dirs = set()
        for p in setup_paths:
            if p:
                package_dirs.add(Path(p).parent)
        for p in pyproject_paths:
            if p and _pyproject_toml_is_package(p):
                package_dirs.add(Path(p).parent)
        return sorted(package_dirs)
