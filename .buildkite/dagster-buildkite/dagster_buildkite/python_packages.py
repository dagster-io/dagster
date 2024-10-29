# pyright: reportUnnecessaryTypeIgnoreComment=false

import logging
import subprocess
from distutils import core as distutils_core
from importlib import reload
from pathlib import Path
from typing import Dict, Optional, Set

import tomli
from pkg_resources import Requirement, parse_requirements

from dagster_buildkite.git import ChangedFiles, GitInfo

changed_filetypes = [".py", ".cfg", ".toml", ".yaml", ".ipynb", ".yml", ".ini", ".jinja"]


def _path_is_relative_to(p: Path, u: Path) -> bool:
    # see https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to
    return u == p or u in p.parents


class PythonPackage:
    def __init__(self, setup_path: Path):
        self.directory = setup_path

        if (setup_path / "setup.py").exists():
            # run_setup stores state in a global variable. Reload the module
            # each time we use it - otherwise we'll get the previous invocation's
            # distribution if our setup.py doesn't implement setup() correctly
            reload(distutils_core)

            distribution = distutils_core.run_setup(str(setup_path / "setup.py"), stop_after="init")

            self._install_requires = distribution.install_requires  # type: ignore[attr-defined]
            self._extras_require = distribution.extras_require  # type: ignore[attr-defined]
            self.name = distribution.get_name()
        else:
            pyproject_toml = setup_path / "pyproject.toml"
            assert (
                pyproject_toml.exists()
            ), f"expected pyproject.toml to exist in directory {setup_path}"

            try:
                with open(pyproject_toml, "rb") as f:
                    project = tomli.load(f)["project"]
            except KeyError:
                # this directory has a pyproject.toml but isn't really a python projects,
                # ie docs/
                self.name = setup_path.name
                self._install_requires = []
                self._extras_require = {}
            else:
                self.name = project["name"]
                self._install_requires = project.get("dependencies", [])
                self._extras_require = project.get("optional-dependencies", {})

    @property
    def install_requires(self) -> Set[Requirement]:
        return set(
            requirement
            for requirement in parse_requirements(self._install_requires)
            if PythonPackages.get(requirement.name)  # type: ignore[attr-defined]
        )

    @property
    def extras_require(self) -> Dict[str, Set[Requirement]]:
        extras_require = {}
        for extra, requirements in self._extras_require.items():
            extras_require[extra] = set(
                requirement
                for requirement in parse_requirements(requirements)
                if PythonPackages.get(requirement.name)  # type: ignore[attr-defined]
            )
        return extras_require

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


class PythonPackages:
    _repositories: Set[Path] = set()
    all: Dict[str, PythonPackage] = dict()
    with_changes: Set[PythonPackage] = set()

    @classmethod
    def get(cls, name: str) -> Optional[PythonPackage]:
        # We're inconsistent about whether we use dashes or undrescores and we
        # get away with it because pip converts all underscores to dashes. So
        # mimic that behavior.
        return (
            cls.all.get(name)
            or cls.all.get(name.replace("_", "-"))
            or cls.all.get(name.replace("-", "_"))
        )

    @classmethod
    def walk_dependencies(cls, requirement: Requirement) -> Set[PythonPackage]:
        dependencies: Set[PythonPackage] = set()
        dagster_package = cls.get(requirement.name)  # type: ignore[attr-defined]

        # Return early if it's not a dependency defined in our repo
        if not dagster_package:
            return dependencies

        # Add the dagster package
        dependencies.add(dagster_package)

        # Walk the tree for any extras we require
        for extra in requirement.extras:
            for req in dagster_package.extras_require.get(extra, set()):
                dependencies.update(cls.walk_dependencies(req))

        # Walk the tree for anything our dagster package's install requires
        for req in dagster_package.install_requires:
            dependencies.update(cls.walk_dependencies(req))

        return dependencies

    @classmethod
    def load_from_git(cls, git_info: GitInfo) -> None:
        # Only do the expensive globbing once
        if git_info.directory in cls._repositories:
            return None

        ChangedFiles.load_from_git(git_info)

        logging.info("Finding Python packages:")

        # Consider any setup.py file to be a package
        output = subprocess.check_output(
            ["git", "ls-files", "."],
            cwd=str(git_info.directory),
        ).decode("utf-8")
        processed = set()
        packages = []
        for file in output.split("\n"):
            if not file:
                continue
            path_dir = (git_info.directory / Path(file)).parents[0]
            if str(path_dir) in processed:
                continue
            processed |= {str(path_dir)}
            assert path_dir.is_dir()
            if (path_dir / "setup.py").exists() or (path_dir / "pyproject.toml").exists():
                try:
                    packages.append(PythonPackage(path_dir))
                except:
                    logging.exception(f"Failed processing python package at {path_dir}")
                    raise

        for package in sorted(packages):
            logging.info("  - " + package.name)
            cls.all[package.name] = package

        packages_with_changes: Set[PythonPackage] = set()

        logging.info("Finding changed packages:")
        for package in packages:
            for change in ChangedFiles.all:
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
            cls.with_changes.add(package)
