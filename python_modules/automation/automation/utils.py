import os
import shutil
import subprocess
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

import click


def check_output(cmd: list[str], dry_run: bool = True, cwd: str | None = None) -> str | None:
    if dry_run:
        click.echo(
            click.style("Dry run; not running.", fg="red") + " Would run: {}".format(" ".join(cmd))
        )
        return None
    else:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, cwd=cwd)


def which_(exe: str) -> str | None:
    """Uses shutil to look for an executable, mimicking unix which."""
    # Replaced distutils.spawn with shutil.which for Python 3.12+ compatibility
    return shutil.which(exe)


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
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return "\n[project]" in content or content.startswith("[project]")


# These are directories that contain setup.py or pyproject.toml files but are
# not actually packages we want to enforce py.typed files for. For example,
# sample repos that are only used for testing and not published as packages.
_EXCLUDE_PATTERNS = ["/sample-repos/"]


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
            if p and not any(exclude in p for exclude in _EXCLUDE_PATTERNS):
                package_dirs.add(Path(p).parent)
        for p in pyproject_paths:
            if (
                p
                and _pyproject_toml_is_package(p)
                and not any(exclude in p for exclude in _EXCLUDE_PATTERNS)
            ):
                package_dirs.add(Path(p).parent)
        return sorted(package_dirs)
