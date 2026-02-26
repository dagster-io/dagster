# The ignore below is not valid in the dagster repo, but is valid in the internal repo
# so we need this to suppress a pyright error in dagster buildkite
# pyright: reportUnnecessaryTypeIgnoreComment=false
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

import tomllib  # requires Python 3.11+
from packaging.requirements import Requirement


def parse_requirements(lines: list[str]) -> list[Requirement]:
    return [
        Requirement(line) for line in lines if line.strip() and not line.strip().startswith("#")
    ]


changed_filetypes = [
    ".py",
    ".cfg",
    ".toml",
    ".yaml",
    ".ipynb",
    ".yml",
    ".ini",
    ".jinja",
]


def _path_is_relative_to(p: Path, u: Path) -> bool:
    # see https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to
    return u == p or u in p.parents


class PythonPackage:
    def __init__(self, setup_path: Path):
        self.directory = setup_path

        pyproject_toml = setup_path / "pyproject.toml"

        # Prefer pyproject.toml over setup.py. This supports the migration from
        # setup.py to pyproject.toml - packages may have both during transition.
        if pyproject_toml.exists():
            try:
                with open(pyproject_toml, "rb") as f:
                    project = tomllib.load(f)["project"]
            except KeyError:
                # this directory has a pyproject.toml but isn't really a python project,
                # ie docs/
                self.name = setup_path.name
                self.dependencies = []
                self.optional_dependencies = {}
            else:
                self.name = project["name"]
                self.dependencies = project.get("dependencies", [])
                self.optional_dependencies = project.get("optional-dependencies", {})
        elif (setup_path / "setup.py").exists():
            # Legacy fallback using distutils (deprecated in 3.10, removed in 3.12)
            # Import lazily to avoid import error on Python 3.12+
            from distutils import (
                core as distutils_core,  # pyright: ignore[reportAttributeAccessIssue]
            )
            from importlib import reload

            # run_setup stores state in a global variable. Reload the module
            # each time we use it - otherwise we'll get the previous invocation's
            # distribution if our setup.py doesn't implement setup() correctly
            reload(distutils_core)

            distribution = distutils_core.run_setup(str(setup_path / "setup.py"), stop_after="init")

            self.dependencies = distribution.install_requires or []  # type: ignore[attr-defined]
            self.optional_dependencies = distribution.extras_require or {}  # type: ignore[attr-defined]
            self.name = distribution.get_name()
        else:
            raise ValueError(
                f"expected pyproject.toml or setup.py to exist in directory {setup_path}"
            )

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"PythonPackage({self.name})"

    def __eq__(self, other):
        return self.directory == other.directory

    # Because we define __eq__
    # https://docs.python.org/3.1/reference/datamodel.html#object.__hash__
    def __hash__(self):
        return hash(self.directory)

    def __lt__(self, other):
        return self.name < other.name


def _discover_packages(repo_path: Path) -> list[PythonPackage]:
    """Discover all Python packages in the git repository."""
    logging.info("Finding Python packages:")

    output = subprocess.check_output(
        ["git", "ls-files", "."],
        cwd=str(repo_path),
    ).decode("utf-8")
    processed = set()
    packages = []
    for file in output.split("\n"):
        if not file:
            continue
        path_dir = (repo_path / Path(file)).parents[0]
        if str(path_dir) in processed:
            continue
        processed |= {str(path_dir)}
        assert path_dir.is_dir(), f"expected {path_dir} to be a directory"
        if (path_dir / "setup.py").exists() or (path_dir / "pyproject.toml").exists():
            try:
                packages.append(PythonPackage(path_dir))
            except:
                logging.exception(f"Failed processing python package at {path_dir}")
                raise

    for package in sorted(packages):
        logging.info("  - " + package.name)

    return packages


def _find_packages_with_changes(
    packages: list[PythonPackage], changed_files: frozenset[Path]
) -> set[PythonPackage]:
    """Find packages that have changed based on the changed files."""
    packages_with_changes: set[PythonPackage] = set()

    logging.info("Finding changed packages:")
    for package in packages:
        for change in changed_files:
            if (
                # Our change is in this package's directory
                _path_is_relative_to(change, package.directory)
                # The file can alter behavior - exclude things like README changes
                and (change.suffix in changed_filetypes)
                # The file is not part of a test suite. We treat this differently
                # because we don't want to run tests in dependent packages
                and "_tests/" not in str(change)
            ):
                packages_with_changes.add(package)

    for package in sorted(packages_with_changes):
        logging.info("  - " + package.name)

    return packages_with_changes


@dataclass
class PythonPackagesData:
    all: dict[str, PythonPackage]
    with_changes: frozenset[PythonPackage]

    def get(self, name: str) -> PythonPackage | None:
        # We're inconsistent about whether we use dashes or underscores and we
        # get away with it because pip converts all underscores to dashes. So
        # mimic that behavior.
        return (
            self.all.get(name)
            or self.all.get(name.replace("_", "-"))
            or self.all.get(name.replace("-", "_"))
        )

    def walk_dependencies(self, requirement: Requirement) -> set[PythonPackage]:
        dependencies: set[PythonPackage] = set()
        dagster_package = self.get(requirement.name)

        # Return early if it's not a dependency defined in our repo
        if not dagster_package:
            return dependencies

        # Add the dagster package
        dependencies.add(dagster_package)

        # Walk the tree for any extras we require (using raw requirements;
        # filtering to in-repo packages happens via self.get() above)
        for extra in requirement.extras:
            for req in parse_requirements(dagster_package.optional_dependencies.get(extra, [])):
                dependencies.update(self.walk_dependencies(req))

        # Walk the tree for anything our dagster package's install requires
        for req in parse_requirements(dagster_package.dependencies):
            dependencies.update(self.walk_dependencies(req))

        return dependencies

    @classmethod
    def load(cls, repo_path: Path, all_changed_files: frozenset[Path]) -> "PythonPackagesData":
        packages = _discover_packages(repo_path)
        all_packages: dict[str, PythonPackage] = {pkg.name: pkg for pkg in sorted(packages)}
        packages_with_changes = _find_packages_with_changes(packages, all_changed_files)
        return cls(all=all_packages, with_changes=frozenset(packages_with_changes))
