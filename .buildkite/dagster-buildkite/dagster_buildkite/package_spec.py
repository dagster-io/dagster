import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Mapping, Optional, Union

import pkg_resources
from typing_extensions import TypeAlias

from dagster_buildkite.git import ChangedFiles
from dagster_buildkite.python_packages import PythonPackages, changed_filetypes
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import BuildkiteQueue
from dagster_buildkite.steps.tox import build_tox_step
from dagster_buildkite.utils import (
    BuildkiteLeafStep,
    BuildkiteTopLevelStep,
    GroupStep,
    is_command_step,
    is_feature_branch,
    message_contains,
)

_CORE_PACKAGES = [
    "python_modules/dagster",
    "python_modules/dagit",
    "python_modules/dagster-graphql",
    "js_modules/dagster-ui",
]

_INFRASTRUCTURE_PACKAGES = [
    ".buildkite/dagster-buildkite",
    "python_modules/automation",
    "python_modules/dagster-test",
    "python_modules/docs/dagster-ui-screenshot",
]


def _infer_package_type(directory: str) -> str:
    if directory in _CORE_PACKAGES:
        return "core"
    elif directory.startswith("examples/"):
        return "example"
    elif directory.startswith("python_modules/libraries/"):
        return "extension"
    elif directory in _INFRASTRUCTURE_PACKAGES or directory.startswith("integration_tests"):
        return "infrastructure"
    else:
        return "unknown"


# The list of all available emojis is here:
#   https://github.com/buildkite/emojis#emoji-reference
_PACKAGE_TYPE_TO_EMOJI_MAP: Mapping[str, str] = {
    "core": ":dagster:",
    "example": ":large_blue_diamond:",
    "extension": ":electric_plug:",
    "infrastructure": ":gear:",
    "unknown": ":grey_question:",
}

PytestExtraCommandsFunction: TypeAlias = Callable[
    [AvailablePythonVersion, Optional[str]], List[str]
]
PytestDependenciesFunction: TypeAlias = Callable[[AvailablePythonVersion, Optional[str]], List[str]]
UnsupportedVersionsFunction: TypeAlias = Callable[[Optional[str]], List[AvailablePythonVersion]]


@dataclass
class PackageSpec:
    """Main spec for testing Dagster Python packages using tox.

    Args:
        directory (str): Python directory to test, relative to the repository root. Should contain a
            tox.ini file.
        name (str, optional): Used in the buildkite label. Defaults to None
            (uses the package name as the label).
        package_type (str, optional): Used to determine the emoji attached to the buildkite label.
            Possible values are "core", "example", "extension", and "infrastructure". By default it
            is inferred from the location of the passed directory.
        unsupported_python_versions (List[AvailablePythonVersion], optional): Python versions that
            are not supported by this package. The versions for which pytest will be run are
            the versions determined for the commit minus this list. If this result is empty, then
            the lowest supported version will be tested. Defaults to None (all versions are supported).
        pytest_extra_cmds (Callable[str, List[str]], optional): Optional specification of
            commands to run before the main pytest invocation through tox. Can be either a list of
            commands or a function. Function form takes two arguments, the python version being
            tested and the tox factor (if any), and returns a list of shell commands to execute.
            Defaults to None (no additional commands).
        pytest_step_dependencies (Callable[str, List[str]], optional): Optional specification of
            Buildkite dependencies (e.g. on test image build step) for pytest steps. Can be either a
            list of commands or a function. Function form takes two arguments, the python version
            being tested and the tox factor (if any), and returns a list of Buildkite step names.
            Defaults to None (no additional commands).
        pytest_tox_factors: (List[str], optional): List of additional tox environment factors to
            use when iterating pytest tox environments. A separate pytest step is generated for each
            element of the product of versions tested and these factors. For example, if we are
            testing Python 3.7 and 3.8 and pass factors `["a", "b"]`, then four steps will be
            generated corresponding to environments "py37-a", "py37-b", "py38-a", "py38-b". Defaults
            to None.
        env_vars (List[str], optional): Additional environment variables to pass through to each
            test environment. These must also be listed in the target toxfile under `passenv`.
            Defaults to None.
        tox_file (str, optional): The tox file to use. Defaults to {directory}/tox.ini.
        retries (int, optional): Whether to retry these tests on failure
            for packages of type "core" or "library", disabled for other packages.
        timeout_in_minutes (int, optional): Fail after this many minutes.
        queue (BuildkiteQueue, optional): Schedule steps to this queue.
        run_pytest (bool, optional): Whether to run pytest. Enabled by default.
    """

    directory: str
    name: Optional[str] = None
    package_type: Optional[str] = None
    unsupported_python_versions: Optional[
        Union[List[AvailablePythonVersion], UnsupportedVersionsFunction]
    ] = None
    pytest_extra_cmds: Optional[Union[List[str], PytestExtraCommandsFunction]] = None
    pytest_step_dependencies: Optional[Union[List[str], PytestDependenciesFunction]] = None
    pytest_tox_factors: Optional[List[str]] = None
    env_vars: Optional[List[str]] = None
    tox_file: Optional[str] = None
    retries: Optional[int] = None
    timeout_in_minutes: Optional[int] = None
    queue: Optional[BuildkiteQueue] = None
    run_pytest: bool = True
    always_run_if: Optional[Callable[[], bool]] = None

    def __post_init__(self):
        if not self.name:
            self.name = os.path.basename(self.directory)

        if not self.package_type:
            self.package_type = _infer_package_type(self.directory)

        self._should_skip = None
        self._skip_reason = None

    def build_steps(self) -> List[BuildkiteTopLevelStep]:
        base_name = self.name or os.path.basename(self.directory)
        steps: List[BuildkiteLeafStep] = []

        if self.run_pytest:
            default_python_versions = AvailablePythonVersion.get_pytest_defaults()

            tox_factors: List[Optional[str]] = (
                [f.lstrip("-") for f in self.pytest_tox_factors]
                if self.pytest_tox_factors
                else [None]
            )

            for other_factor in tox_factors:
                if callable(self.unsupported_python_versions):
                    unsupported_python_versions = self.unsupported_python_versions(other_factor)
                else:
                    unsupported_python_versions = self.unsupported_python_versions or []

                supported_python_versions = [
                    v
                    for v in AvailablePythonVersion.get_all()
                    if v not in unsupported_python_versions
                ]

                pytest_python_versions = sorted(
                    list(set(default_python_versions) - set(unsupported_python_versions))
                )
                # Use highest supported python version if no defaults_match
                if len(pytest_python_versions) == 0:
                    pytest_python_versions = [supported_python_versions[-1]]

                for py_version in pytest_python_versions:
                    version_factor = AvailablePythonVersion.to_tox_factor(py_version)
                    if other_factor is None:
                        tox_env = version_factor
                    else:
                        tox_env = f"{version_factor}-{other_factor}"

                    if isinstance(self.pytest_extra_cmds, list):
                        extra_commands_pre = self.pytest_extra_cmds
                    elif callable(self.pytest_extra_cmds):
                        extra_commands_pre = self.pytest_extra_cmds(py_version, other_factor)
                    else:
                        extra_commands_pre = []

                    dependencies = []
                    if not self.skip_reason:
                        if isinstance(self.pytest_step_dependencies, list):
                            dependencies = self.pytest_step_dependencies
                        elif callable(self.pytest_step_dependencies):
                            dependencies = self.pytest_step_dependencies(py_version, other_factor)

                    steps.append(
                        build_tox_step(
                            self.directory,
                            tox_env,
                            base_label=base_name,
                            command_type="pytest",
                            python_version=py_version,
                            env_vars=self.env_vars,
                            extra_commands_pre=extra_commands_pre,
                            dependencies=dependencies,
                            tox_file=self.tox_file,
                            timeout_in_minutes=self.timeout_in_minutes,
                            queue=self.queue,
                            retries=self.retries,
                            skip_reason=self.skip_reason,
                        )
                    )

        emoji = _PACKAGE_TYPE_TO_EMOJI_MAP[self.package_type]  # type: ignore[index]
        if len(steps) >= 2:
            return [
                GroupStep(
                    group=f"{emoji} {base_name}",
                    key=base_name,
                    steps=steps,
                )
            ]
        elif len(steps) == 1:
            only_step = steps[0]
            if not is_command_step(only_step):
                raise ValueError("Expected only step to be a CommandStep")
            return [only_step]
        else:
            return []

    @property
    def requirements(self):
        # First try to infer requirements from the python package
        package = PythonPackages.get(self.name)
        if package:
            return set.union(package.install_requires, *package.extras_require.values())

        # If we don't have a distribution (like many of our integration test suites)
        # we can use a buildkite_deps.txt file to capture requirements
        buildkite_deps_txt = Path(self.directory) / "buildkite_deps.txt"
        if buildkite_deps_txt.exists():
            parsed = pkg_resources.parse_requirements(buildkite_deps_txt.read_text())
            return [requirement for requirement in parsed]

        # Otherwise return nothing
        return []

    @property
    def skip_reason(self) -> Optional[str]:
        # Memoize so we don't log twice
        if self._should_skip is False:
            return None

        if self.always_run_if and self.always_run_if():
            self._should_skip = False
            return None

        if self._skip_reason:
            return self._skip_reason

        if message_contains("NO_SKIP"):
            logging.info(f"Building {self.name} because NO_SKIP set")
            self._should_skip = False
            return None

        if not is_feature_branch(os.getenv("BUILDKITE_BRANCH", "")):
            logging.info(f"Building {self.name} we're not on a feature branch")
            self._should_skip = False
            return None

        for change in ChangedFiles.all:
            if (
                # Our change is in this package's directory
                (Path(self.directory) in change.parents)
                # The file can alter behavior - exclude things like README changes
                # which we tend to include in .md files
                and change.suffix in changed_filetypes
            ):
                logging.info(f"Building {self.name} because it has changed")
                self._should_skip = False
                return None

        # Consider anything required by install or an extra to be in scope.
        # We might one day narrow this down to specific extras.
        for requirement in self.requirements:
            in_scope_changes = PythonPackages.with_changes.intersection(
                PythonPackages.walk_dependencies(requirement)
            )
            if in_scope_changes:
                logging.info(f"Building {self.name} because of changes to {in_scope_changes}")
                self._should_skip = False
                return None

        self._skip_reason = "Package unaffected by these changes"
        self._should_skip = True
        return self._skip_reason
