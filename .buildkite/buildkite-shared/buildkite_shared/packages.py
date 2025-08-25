import logging
import os
from pathlib import Path
from typing import Callable, Optional

import pkg_resources
from buildkite_shared.environment import is_feature_branch, run_all_tests
from buildkite_shared.git import ChangedFiles
from buildkite_shared.python_packages import PythonPackages, changed_filetypes


def requirements(name: str, directory: str):
    # First try to infer requirements from the python package
    package = PythonPackages.get(name)
    if package:
        return set.union(package.install_requires, *package.extras_require.values())

    # If we don't have a distribution (like many of our integration test suites)
    # we can use a buildkite_deps.txt file to capture requirements
    buildkite_deps_txt = Path(directory) / "buildkite_deps.txt"
    if buildkite_deps_txt.exists():
        parsed = pkg_resources.parse_requirements(buildkite_deps_txt.read_text())
        return [requirement for requirement in parsed]

    # Otherwise return nothing
    return []


def skip_reason(
    directory: str,
    name: Optional[str] = None,
    always_run_if: Optional[Callable[[], bool]] = None,
    skip_if: Optional[Callable[[], Optional[str]]] = None,
) -> Optional[str]:
    """Provides a message if this package's steps should be skipped on this run, and no message if the package's steps should be run.
    We actually use this to determine whether or not to run the package.
    """
    if name is None:
        name = os.path.basename(directory)

    # If the result is not cached, check for NO_SKIP signifier first, so that it always
    # takes precedent.
    if run_all_tests():
        logging.info(f"Building {name} because NO_SKIP set")
        return None
    if always_run_if and always_run_if():
        return None
    if skip_if and skip_if():
        return skip_if()

    # Take account of feature_branch changes _after_ skip_if so that skip_if
    # takes precedent. This way, integration tests can run on branch but won't be
    # forced to run on every master commit.
    if not is_feature_branch(os.getenv("BUILDKITE_BRANCH", "")):
        logging.info(f"Building {name} we're not on a feature branch")
        return None

    for change in ChangedFiles.all:
        if (
            # Our change is in this package's directory
            (Path(directory) in change.parents)
            # The file can alter behavior - exclude things like README changes
            # which we tend to include in .md files
            and change.suffix in changed_filetypes
        ):
            logging.info(f"Building {name} because it has changed")
            return None

    # Consider anything required by install or an extra to be in scope.
    # We might one day narrow this down to specific extras.
    for requirement in requirements(name, directory):
        in_scope_changes = PythonPackages.with_changes.intersection(
            PythonPackages.walk_dependencies(requirement)
        )
        if in_scope_changes:
            logging.info(f"Building {name} because of changes to {in_scope_changes}")
            return None

    return "Package unaffected by these changes"
