import glob
import logging
from distutils import core as distutils_core  # pylint: disable=deprecated-module
from importlib import reload
from pathlib import Path
from typing import Set

from dagster_buildkite.utils import get_changed_files
from pkg_resources import Requirement, parse_requirements


class PythonPackage:
    def __init__(self, setup_py_path: Path):
        self.directory = setup_py_path.parent

        # run_setup stores state in a global variable. Reload the module
        # each time we use it - otherwise we'll get the previous invocation's
        # distribution if our setup.py doesn't implement setup() correctly
        reload(distutils_core)
        distribution = distutils_core.run_setup(str(setup_py_path), stop_after="init")

        self._install_requires = distribution.install_requires  # type: ignore[attr-defined]
        self._extras_require = distribution.extras_require  # type: ignore[attr-defined]
        self.name = distribution.get_name()  # type: ignore[attr-defined]

    @property
    def install_requires(self):
        return set(
            requirement
            for requirement in parse_requirements(self._install_requires)
            if get(requirement.name)  # type: ignore[attr-defined]
        )

    @property
    def extras_require(self):
        extras_require = {}
        for extra, requirements in self._extras_require.items():
            extras_require[extra] = set(
                requirement
                for requirement in parse_requirements(requirements)
                if get(requirement.name)
            )
        return extras_require

    def __repr__(self):
        return self.name


# Consider any setup.py file to be a package
_packages = set(
    [
        PythonPackage(Path(setup))
        for setup in glob.glob("**/setup.py", recursive=True)
        if "_tests" not in setup
    ]
)
# hidden files are ignored by glob.glob and we don't actually want to recurse
# all hidden files because there's so much random cruft. So just hardcode the
# one hidden package we know we need.
_packages.add(PythonPackage(Path(".buildkite/dagster-buildkite/setup.py")))

_registry = {package.name: package for package in _packages}

with_changes = set()

for package in _packages:
    for change in get_changed_files():
        if (
            # Our change is in this package's directory
            (change in package.directory.rglob("*"))
            # The file can alter behavior - exclude things like README changes
            and (change.suffix in [".py", ".cfg", ".toml"])
            # The file is not part of a test suite. We treat this differently
            # because we don't want to run tests in dependent packages
        ):
            with_changes.add(package)

logging.info("Changed packages:")
for package in with_changes:
    logging.info(package.name)


def get(name: str):
    return _registry.get(name)


def walk_dependencies(requirement: Requirement):
    dependencies: Set[PythonPackage] = set()
    dagster_package = get(requirement.name)  # type: ignore[attr-defined]

    # Return early if it's not a dependency defined in our repo
    if not dagster_package:
        return dependencies

    # Add the dagster package
    dependencies.add(dagster_package)

    # Walk the tree for any extras we require
    for extra in requirement.extras:
        for req in dagster_package.extras_require.get(extra):
            dependencies.update(walk_dependencies(req))

    # Walk the tree for anything our dagster package's install requires
    for req in dagster_package.install_requires:
        dependencies.update(walk_dependencies(req))

    return dependencies
