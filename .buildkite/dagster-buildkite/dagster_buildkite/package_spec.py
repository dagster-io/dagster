import os
from typing import Callable, List, Mapping, NamedTuple, Optional, Union

from .python_version import AvailablePythonVersion
from .step_builder import BuildkiteQueue
from .steps.tox import build_tox_step
from .utils import BuildkiteLeafStep, GroupStep

_CORE_PACKAGES = [
    "python_modules/dagster",
    "python_modules/dagit",
    "python_modules/dagster-graphql",
    "js_modules/dagit",
]

_INFRASTRUCTURE_PACKAGES = [
    ".buildkite/dagster-buildkite",
    "python_modules/automation",
    "python_modules/dagster-test",
    "scripts",
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

PytestExtraCommandsFunction = Callable[[AvailablePythonVersion, Optional[str]], List[str]]
PytestDependenciesFunction = Callable[[AvailablePythonVersion, Optional[str]], List[str]]


class PackageSpec(
    NamedTuple(
        "_PackageSpec",
        [
            ("directory", str),
            ("name", str),
            ("package_type", str),
            ("unsupported_python_versions", List[AvailablePythonVersion]),
            ("pytest_extra_cmds", Optional[Union[List[str], PytestExtraCommandsFunction]]),
            ("pytest_step_dependencies", Optional[Union[List[str], PytestDependenciesFunction]]),
            ("pytest_tox_factors", Optional[List[str]]),
            ("env_vars", List[str]),
            ("tox_file", Optional[str]),
            ("retries", Optional[int]),
            ("upload_coverage", bool),
            ("timeout_in_minutes", Optional[int]),
            ("queue", Optional[BuildkiteQueue]),
            ("run_pytest", bool),
            ("run_mypy", bool),
            ("run_pylint", bool),
        ],
    )
):
    """Main spec for testing Dagster Python packages using tox.

    Args:
        directory (str): Python directory to test, relative to the repository root. Should contain a
            tox.ini file.
        name (str, optional): Used in the buildkite label and coverage filename. Defaults to None
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
        upload_coverage (bool, optional): Whether to copy coverage artifacts. By default, enabled
            for packages of type "core" or "library", disabled for other packages.
        timeout_in_minutes (int, optional): Fail after this many minutes.
        queue (BuildkiteQueue, optional): Schedule steps to this queue.
        run_pytest (bool, optional): Whether to run pytest. Enabled by default.
        run_mypy (bool, optional): Whether to run mypy. Runs in the highest available supported
            Python version. Enabled by default.
        run_pylint (bool, optional): Whether to run pylint. Runs in the highest available supported
            Python version. Enabled by default.
    """

    def __new__(
        cls,
        directory: str,
        name: Optional[str] = None,
        package_type: Optional[str] = None,
        unsupported_python_versions: Optional[List[AvailablePythonVersion]] = None,
        pytest_extra_cmds: Optional[Union[List[str], PytestExtraCommandsFunction]] = None,
        pytest_step_dependencies: Optional[Union[List[str], PytestDependenciesFunction]] = None,
        pytest_tox_factors: Optional[List[str]] = None,
        env_vars: Optional[List[str]] = None,
        tox_file: Optional[str] = None,
        retries: Optional[int] = None,
        upload_coverage: Optional[bool] = None,
        timeout_in_minutes: Optional[int] = None,
        queue: Optional[BuildkiteQueue] = None,
        run_pytest: bool = True,
        run_mypy: bool = True,
        run_pylint: bool = True,
    ):
        package_type = package_type or _infer_package_type(directory)
        return super(PackageSpec, cls).__new__(
            cls,
            directory,
            name or os.path.basename(directory),
            package_type,
            unsupported_python_versions or [],
            pytest_extra_cmds,
            pytest_step_dependencies,
            pytest_tox_factors,
            env_vars or [],
            tox_file,
            retries,
            upload_coverage if upload_coverage is not None else package_type in ("core", "library"),
            timeout_in_minutes,
            queue,
            run_pytest,
            run_mypy,
            run_pylint,
        )

    def build_steps(self) -> List[GroupStep]:
        base_name = self.name or os.path.basename(self.directory)
        steps: List[BuildkiteLeafStep] = []

        supported_python_versions = [
            v for v in AvailablePythonVersion.get_all() if v not in self.unsupported_python_versions
        ]

        if self.run_pytest:

            default_python_versions = AvailablePythonVersion.get_pytest_defaults()
            pytest_python_versions = sorted(
                list(set(default_python_versions) - set(self.unsupported_python_versions))
            )
            # Use lowest supported python version if no defaults match.
            if len(pytest_python_versions) == 0:
                pytest_python_versions = [supported_python_versions[0]]

            tox_factors: List[Optional[str]] = (
                [f.lstrip("-") for f in self.pytest_tox_factors]
                if self.pytest_tox_factors
                else [None]
            )

            for py_version in pytest_python_versions:
                for other_factor in tox_factors:

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

                    if self.upload_coverage:
                        coverage_id = f"{base_name}-{other_factor}" if other_factor else base_name
                        coverage = f".coverage.{coverage_id}.{py_version}.$BUILDKITE_BUILD_ID"
                        extra_commands_post = [
                            f"mv .coverage {coverage}",
                            f"buildkite-agent artifact upload {coverage}",
                        ]
                    else:
                        extra_commands_post = []

                    if isinstance(self.pytest_step_dependencies, list):
                        dependencies = self.pytest_step_dependencies
                    elif callable(self.pytest_step_dependencies):
                        dependencies = self.pytest_step_dependencies(py_version, other_factor)
                    else:
                        dependencies = []

                    steps.append(
                        build_tox_step(
                            self.directory,
                            tox_env,
                            base_label=base_name,
                            command_type="pytest",
                            python_version=py_version,
                            env_vars=self.env_vars,
                            extra_commands_pre=extra_commands_pre,
                            extra_commands_post=extra_commands_post,
                            dependencies=dependencies,
                            tox_file=self.tox_file,
                            timeout_in_minutes=self.timeout_in_minutes,
                            queue=self.queue,
                            retries=self.retries,
                        )
                    )

        if self.run_mypy:
            steps.append(
                build_tox_step(
                    self.directory,
                    "mypy",
                    base_label=base_name,
                    command_type="mypy",
                    python_version=supported_python_versions[-1],
                )
            )

        if self.run_pylint:
            steps.append(
                build_tox_step(
                    self.directory,
                    "pylint",
                    base_label=base_name,
                    command_type="pylint",
                    python_version=supported_python_versions[-1],
                )
            )

        emoji = _PACKAGE_TYPE_TO_EMOJI_MAP[self.package_type]
        return [
            GroupStep(
                group=f"{emoji} {base_name}",
                key=base_name,
                steps=steps,
            )
        ]
