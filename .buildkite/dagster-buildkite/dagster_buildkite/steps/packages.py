import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Callable, Optional, Union

from buildkite_shared.packages import skip_reason
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import BuildkiteQueue
from buildkite_shared.step_builders.group_step_builder import (
    GroupLeafStepConfiguration,
    GroupStepBuilder,
)
from buildkite_shared.step_builders.step_builder import (
    StepConfiguration,
    TopLevelStepConfiguration,
    is_command_step,
)
from dagster_buildkite.defines import GCP_CREDS_FILENAME, GCP_CREDS_LOCAL_FILE, GIT_REPO_ROOT
from dagster_buildkite.steps.test_project import test_project_depends_fn
from dagster_buildkite.steps.tox import ToxFactor, build_tox_step
from dagster_buildkite.utils import (
    connect_sibling_docker_container,
    has_component_integration_changes,
    has_dagster_airlift_changes,
    has_dg_changes,
    has_storage_test_fixture_changes,
    network_buildkite_container,
    skip_if_not_dagster_dbt_cloud_commit,
    skip_if_not_dagster_dbt_commit,
)
from typing_extensions import TypeAlias

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
    [AvailablePythonVersion, Optional[ToxFactor]], list[str]
]
PytestDependenciesFunction: TypeAlias = Callable[
    [AvailablePythonVersion, Optional[ToxFactor]], list[str]
]
UnsupportedVersionsFunction: TypeAlias = Callable[
    [Optional[ToxFactor]], list[AvailablePythonVersion]
]


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
        unsupported_python_versions (list[AvailablePythonVersion], optional): Python versions that
            are not supported by this package. The versions for which pytest will be run are
            the versions determined for the commit minus this list. If this result is empty, then
            the lowest supported version will be tested. Defaults to None (all versions are supported).
        pytest_extra_cmds (Callable[str, list[str]], optional): Optional specification of
            commands to run before the main pytest invocation through tox. Can be either a list of
            commands or a function. Function form takes two arguments, the python version being
            tested and the tox factor (if any), and returns a list of shell commands to execute.
            Defaults to None (no additional commands).
        pytest_step_dependencies (Callable[str, list[str]], optional): Optional specification of
            Buildkite dependencies (e.g. on test image build step) for pytest steps. Can be either a
            list of commands or a function. Function form takes two arguments, the python version
            being tested and the tox factor (if any), and returns a list of Buildkite step names.
            Defaults to None (no additional commands).
        pytest_tox_factors: (list[ToxFactor], optional): list of additional tox environment factors to
            use when iterating pytest tox environments. A separate pytest step is generated for each
            element of the product of versions tested and these factors. For example, if we are
            testing Python 3.7 and 3.8 and pass factors `[ToxFactor("pytest"), ToxFactor("integration")]`,
            then four steps will be generated corresponding to environments "py37-pytest", "py37-integration",
            "py38-pytest", "py38-integration". Defaults to None.
        env_vars (list[str], optional): Additional environment variables to pass through to each
            test environment. These must also be listed in the target toxfile under `passenv`.
            Defaults to None.
        tox_file (str, optional): The tox file to use. Defaults to {directory}/tox.ini.
        retries (int, optional): Whether to retry these tests on failure
            for packages of type "core" or "library", disabled for other packages.
        timeout_in_minutes (int, optional): Fail after this many minutes.
        queue (BuildkiteQueue, optional): Schedule steps to this queue.
        run_pytest (bool, optional): Whether to run pytest. Enabled by default.
        splits (int, optional): Number of splits to use when no tox factors are defined.
            This allows parallelizing tests even when no specific tox factors are specified. Defaults to 1.
    """

    directory: str
    name: Optional[str] = None
    package_type: Optional[str] = None
    unsupported_python_versions: Optional[
        Union[list[AvailablePythonVersion], UnsupportedVersionsFunction]
    ] = None
    pytest_extra_cmds: Optional[Union[list[str], PytestExtraCommandsFunction]] = None
    pytest_step_dependencies: Optional[Union[list[str], PytestDependenciesFunction]] = None
    pytest_tox_factors: Optional[list[ToxFactor]] = None
    env_vars: Optional[list[str]] = None
    tox_file: Optional[str] = None
    retries: Optional[int] = None
    timeout_in_minutes: Optional[int] = None
    queue: Optional[BuildkiteQueue] = None
    run_pytest: bool = True
    splits: int = 1
    always_run_if: Optional[Callable[[], bool]] = None
    skip_if: Optional[Callable[[], Optional[str]]] = None

    def __post_init__(self):
        if not self.name:
            self.name = os.path.basename(self.directory)

        if not self.package_type:
            self.package_type = _infer_package_type(self.directory)

        self._should_skip = None
        self._skip_reason = None

    def build_steps(self) -> list[TopLevelStepConfiguration]:
        base_name = self.name or os.path.basename(self.directory)
        steps: list[GroupLeafStepConfiguration] = []

        if self.run_pytest:
            default_python_versions = AvailablePythonVersion.get_pytest_defaults()

            tox_factors: Sequence[Optional[ToxFactor]] = (
                self.pytest_tox_factors if self.pytest_tox_factors else [None]
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

                pytest_python_versions = [
                    AvailablePythonVersion(v)
                    for v in sorted(
                        set(e.value for e in default_python_versions)
                        - set(e.value for e in unsupported_python_versions)
                    )
                ]
                # Use highest supported python version if no defaults_match
                if len(pytest_python_versions) == 0:
                    pytest_python_versions = [supported_python_versions[-1]]

                for py_version in pytest_python_versions:
                    version_factor = AvailablePythonVersion.to_tox_factor(py_version)
                    if other_factor is None:
                        tox_env = version_factor
                        splits = self.splits
                    else:
                        tox_env = f"{version_factor}-{other_factor.factor}"
                        splits = other_factor.splits

                    if isinstance(self.pytest_extra_cmds, list):
                        base_extra_commands_pre = self.pytest_extra_cmds
                    elif callable(self.pytest_extra_cmds):
                        base_extra_commands_pre = self.pytest_extra_cmds(py_version, other_factor)
                    else:
                        base_extra_commands_pre = []

                    dependencies = []
                    if not self.skip_reason:
                        if isinstance(self.pytest_step_dependencies, list):
                            dependencies = self.pytest_step_dependencies
                        elif callable(self.pytest_step_dependencies):
                            dependencies = self.pytest_step_dependencies(py_version, other_factor)

                    # Generate multiple steps if splits > 1
                    for split_index in range(1, splits + 1):
                        if splits > 1:
                            split_label = f"{base_name} ({split_index}/{splits})"
                            pytest_args = [f"--split {split_index}/{splits}"]
                            extra_commands_pre = base_extra_commands_pre
                        else:
                            split_label = base_name
                            pytest_args = None
                            extra_commands_pre = base_extra_commands_pre

                        steps.append(
                            build_tox_step(
                                self.directory,
                                tox_env,
                                base_label=split_label,
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
                                pytest_args=pytest_args,
                            )
                        )

        emoji = _PACKAGE_TYPE_TO_EMOJI_MAP[self.package_type]  # type: ignore[index]
        if len(steps) >= 2:
            return [
                GroupStepBuilder(
                    name=f"{emoji} {base_name}",
                    key=base_name,
                    steps=steps,
                ).build()
            ]
        elif len(steps) == 1:
            only_step = steps[0]
            if not is_command_step(only_step):
                raise ValueError("Expected only step to be a CommandStep")
            return [only_step]
        else:
            return []

    @property
    def skip_reason(self) -> Optional[str]:
        """Provides a message if this package's steps should be skipped on this run, and no message if the package's steps should be run.
        We actually use this to determine whether or not to run the package.

        Because we use an archaic version of python to build our images, we can't use `cached_property`, and so we reinvent the wheel here with
        self._should_skip and self._skip_reason. When we determine definitively that a package should or shouldn't be skipped, we cache the result on self._should_skip
        as a boolean (it starts out as None), and cache the skip reason (or lack thereof) on self._skip_reason.
        """
        # If self._should_skip is not None, then the result is cached on self._skip_reason and we can return it.
        if self._should_skip is not None:
            if self._should_skip is True:
                assert self._skip_reason is not None, (
                    "Expected skip reason to be set if self._should_skip is True."
                )
            return self._skip_reason

        self._skip_reason = skip_reason(self.directory, self.name, self.always_run_if, self.skip_if)
        self._should_skip = self._skip_reason is not None
        return self._skip_reason


def build_example_packages_steps() -> list[StepConfiguration]:
    custom_example_pkg_roots = [pkg.directory for pkg in EXAMPLE_PACKAGES_WITH_CUSTOM_CONFIG]
    example_packages_with_standard_config = [
        PackageSpec(pkg)
        for pkg in (
            _get_uncustomized_pkg_roots("examples", custom_example_pkg_roots)
            + _get_uncustomized_pkg_roots("examples/experimental", custom_example_pkg_roots)
        )
        if pkg not in ("examples/deploy_ecs", "examples/starlift-demo")
    ]

    example_packages = EXAMPLE_PACKAGES_WITH_CUSTOM_CONFIG + example_packages_with_standard_config

    return build_steps_from_package_specs(example_packages)


def build_library_packages_steps() -> list[StepConfiguration]:
    custom_library_pkg_roots = [pkg.directory for pkg in LIBRARY_PACKAGES_WITH_CUSTOM_CONFIG]
    library_packages_with_standard_config = [
        *[
            PackageSpec(pkg)
            for pkg in _get_uncustomized_pkg_roots("python_modules", custom_library_pkg_roots)
        ],
        *[
            PackageSpec(pkg)
            for pkg in _get_uncustomized_pkg_roots(
                "python_modules/libraries", custom_library_pkg_roots
            )
        ],
    ]

    return build_steps_from_package_specs(
        LIBRARY_PACKAGES_WITH_CUSTOM_CONFIG + library_packages_with_standard_config
    )


def build_steps_from_package_specs(
    package_specs: list[PackageSpec],
) -> list[StepConfiguration]:
    steps: list[StepConfiguration] = []
    all_packages = sorted(
        package_specs,
        key=lambda p: f"{_PACKAGE_TYPE_ORDER.index(p.package_type)} {p.name}",  # type: ignore[arg-type]
    )

    for pkg in all_packages:
        steps += pkg.build_steps()

    return steps


_PACKAGE_TYPE_ORDER = ["core", "extension", "example", "infrastructure", "unknown"]


# Find packages under a root subdirectory that are not configured above.
def _get_uncustomized_pkg_roots(root: str, custom_pkg_roots: list[str]) -> list[str]:
    all_files_in_root = [
        os.path.relpath(p, GIT_REPO_ROOT) for p in glob(os.path.join(GIT_REPO_ROOT, root, "*"))
    ]
    return [
        p for p in all_files_in_root if p not in custom_pkg_roots and os.path.exists(f"{p}/tox.ini")
    ]


# ########################
# ##### PACKAGES WITH CUSTOM STEPS
# ########################


def airflow_extra_cmds(version: AvailablePythonVersion, _) -> list[str]:
    return [
        'export AIRFLOW_HOME="/airflow"',
        "mkdir -p $${AIRFLOW_HOME}",
    ]


airline_demo_extra_cmds = [
    "pushd examples/airline_demo",
    # Run the postgres db. We are in docker running docker
    # so this will be a sibling container.
    "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
    # Can't use host networking on buildkite and communicate via localhost
    # between these sibling containers, so pass along the ip.
    *network_buildkite_container("postgres"),
    *connect_sibling_docker_container(
        "postgres", "test-postgres-db-airline", "POSTGRES_TEST_DB_HOST"
    ),
    "popd",
]


def dagster_graphql_extra_cmds(_, tox_factor: Optional[ToxFactor]) -> list[str]:
    if tox_factor and tox_factor.factor.startswith("postgres"):
        return [
            "pushd python_modules/dagster-graphql/dagster_graphql_tests/graphql/",
            "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
            # Can't use host networking on buildkite and communicate via localhost
            # between these sibling containers, so pass along the ip.
            *network_buildkite_container("postgres"),
            *connect_sibling_docker_container(
                "postgres", "test-postgres-db-graphql", "POSTGRES_TEST_DB_HOST"
            ),
            "popd",
        ]
    else:
        return []


deploy_docker_example_extra_cmds = [
    "pushd examples/deploy_docker/from_source",
    "./build.sh",
    "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
    *network_buildkite_container("docker_example_network"),
    *connect_sibling_docker_container(
        "docker_example_network",
        "docker_example_webserver",
        "DEPLOY_DOCKER_WEBSERVER_HOST",
    ),
    "popd",
]


def celery_extra_cmds(version: AvailablePythonVersion, _) -> list[str]:
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version.value,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "pushd python_modules/libraries/dagster-celery",
        # Run the rabbitmq db. We are in docker running docker
        # so this will be a sibling container.
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        *network_buildkite_container("rabbitmq"),
        *connect_sibling_docker_container(
            "rabbitmq", "test-rabbitmq", "DAGSTER_CELERY_BROKER_HOST"
        ),
        "popd",
    ]


def docker_extra_cmds(version: AvailablePythonVersion, _) -> list[str]:
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version.value,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
    ]


ui_extra_cmds = ["make rebuild_ui"]


def has_dg_or_component_integration_changes() -> bool:
    """Check for changes in dagster-dg-cli or in integrations that implement components."""
    return has_dg_changes() or has_component_integration_changes()


mysql_extra_cmds = [
    "pushd python_modules/libraries/dagster-mysql/dagster_mysql_tests/",
    "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
    *network_buildkite_container("mysql"),
    *network_buildkite_container("mysql_pinned"),
    *network_buildkite_container("mysql_pinned_backcompat"),
    *connect_sibling_docker_container("mysql", "test-mysql-db", "MYSQL_TEST_DB_HOST"),
    *connect_sibling_docker_container(
        "mysql_pinned", "test-mysql-db-pinned", "MYSQL_TEST_PINNED_DB_HOST"
    ),
    *connect_sibling_docker_container(
        "mysql_pinned_backcompat",
        "test-mysql-db-pinned-backcompat",
        "MYSQL_TEST_PINNED_BACKCOMPAT_DB_HOST",
    ),
    "popd",
]


def k8s_extra_cmds(version: AvailablePythonVersion, _) -> list[str]:
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version.value,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
    ]


gcp_creds_extra_cmds = (
    [
        rf"aws s3 cp s3://\${{BUILDKITE_SECRETS_BUCKET}}/{GCP_CREDS_FILENAME} "
        + GCP_CREDS_LOCAL_FILE,
        "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
    ]
    if not os.getenv("CI_DISABLE_INTEGRATION_TESTS")
    else []
)


# Some Dagster packages have more involved test configs or support only certain Python version;
# special-case those here
EXAMPLE_PACKAGES_WITH_CUSTOM_CONFIG: list[PackageSpec] = [
    PackageSpec(
        "examples/assets_smoke_test",
    ),
    PackageSpec(
        "examples/deploy_docker",
        pytest_extra_cmds=deploy_docker_example_extra_cmds,
    ),
    PackageSpec(
        "examples/docs_snippets",
        # The docs_snippets test suite also installs a ton of packages in the same environment,
        # which is liable to cause dependency collisions. It's not necessary to test all these
        # snippets in all python versions since we are testing the core code exercised by the
        # snippets against all supported python versions.
        unsupported_python_versions=AvailablePythonVersion.get_all_except_default(),
        pytest_tox_factors=[
            ToxFactor("all"),
            ToxFactor("integrations"),
            ToxFactor("docs_snapshot_test", splits=3),
        ],
        always_run_if=has_dg_changes,
    ),
    PackageSpec(
        "examples/project_fully_featured",
        unsupported_python_versions=[
            AvailablePythonVersion.V3_12,  # duckdb
            AvailablePythonVersion.V3_13,  # duckdb
        ],
    ),
    PackageSpec(
        "examples/with_great_expectations",
        unsupported_python_versions=[
            AvailablePythonVersion.V3_9,
        ],
    ),
    PackageSpec(
        "examples/with_pyspark",
    ),
    PackageSpec(
        "examples/with_pyspark_emr",
    ),
    PackageSpec(
        "examples/with_wandb",
        unsupported_python_versions=[
            # dagster-wandb dep
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ],
    ),
    # The 6 tutorials referenced in cloud onboarding cant test "source" due to dagster-cloud dep
    PackageSpec(
        "examples/assets_modern_data_stack",
        pytest_tox_factors=[ToxFactor("pypi")],
    ),
    PackageSpec(
        "examples/assets_dbt_python",
        pytest_tox_factors=[ToxFactor("pypi")],
        unsupported_python_versions=[
            AvailablePythonVersion.V3_12,  # duckdb
            AvailablePythonVersion.V3_13,  # duckdb
        ],
    ),
    PackageSpec(
        "examples/assets_dynamic_partitions",
        unsupported_python_versions=[
            AvailablePythonVersion.V3_12,  # duckdb
            AvailablePythonVersion.V3_13,  # duckdb
        ],
    ),
    PackageSpec(
        "examples/quickstart_etl",
        pytest_tox_factors=[ToxFactor("pypi")],
    ),
    PackageSpec(
        "examples/use_case_repository",
        pytest_tox_factors=[ToxFactor("source")],
    ),
    # Federation tutorial spins up multiple airflow instances, slow to run - use docker queue to ensure
    # beefier instance
    PackageSpec(
        "examples/airlift-federation-tutorial",
        always_run_if=has_dagster_airlift_changes,
        timeout_in_minutes=30,
        queue=BuildkiteQueue.DOCKER,
        unsupported_python_versions=[
            # airflow
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ],
    ),
    PackageSpec(
        "examples/airlift-migration-tutorial",
        always_run_if=has_dagster_airlift_changes,
        unsupported_python_versions=[
            # airflow
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ],
    ),
]


def _unsupported_dagster_python_versions(
    tox_factor: Optional[ToxFactor],
) -> list[AvailablePythonVersion]:
    if tox_factor and tox_factor.factor == "general_tests_old_protobuf":
        return [
            AvailablePythonVersion.V3_11,
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ]

    if tox_factor and tox_factor.factor in {
        "type_signature_tests",
    }:
        return [AvailablePythonVersion.V3_12]

    return []


def test_subfolders(tests_folder_name: str) -> Iterable[str]:
    tests_path = (
        Path(__file__).parent
        / Path("../../../../python_modules/dagster/dagster_tests/")
        / Path(tests_folder_name)
    )
    for subfolder in tests_path.iterdir():
        if subfolder.suffix == ".py" and subfolder.stem != "__init__":
            raise Exception(
                f"If you are splitting a test folder into parallel subfolders "
                f"there should be no python files in the root of the folder. Found {subfolder}."
            )
        if subfolder.is_dir():
            yield subfolder.name


def tox_factors_for_folder(tests_folder_name: str) -> list[ToxFactor]:
    return [
        ToxFactor(f"{tests_folder_name}__{subfolder_name}")
        for subfolder_name in test_subfolders(tests_folder_name)
    ]


LIBRARY_PACKAGES_WITH_CUSTOM_CONFIG: list[PackageSpec] = [
    PackageSpec(
        "python_modules/automation",
        # automation is internal code that doesn't need to be tested in every python version. The
        # test suite also installs a ton of packages in the same environment, which is liable to
        # cause dependency collisions.
        unsupported_python_versions=AvailablePythonVersion.get_all_except_default(),
        retries=0,
    ),
    PackageSpec("python_modules/dagster-webserver", pytest_extra_cmds=ui_extra_cmds),
    PackageSpec(
        "python_modules/dagster",
        env_vars=["AWS_ACCOUNT_ID"],
        pytest_tox_factors=[
            ToxFactor("api_tests"),
            ToxFactor("asset_defs_tests"),
            ToxFactor("cli_tests", splits=2),
            ToxFactor("components_tests"),
            ToxFactor("core_tests"),
            ToxFactor("daemon_sensor_tests", splits=2),
            ToxFactor("daemon_tests", splits=2),
            ToxFactor("declarative_automation_tests", splits=2),
            ToxFactor("definitions_tests"),
            ToxFactor("general_tests"),
            ToxFactor("general_tests_old_protobuf"),
            ToxFactor("launcher_tests"),
            ToxFactor("logging_tests"),
            ToxFactor("model_tests"),
            ToxFactor("scheduler_tests"),
            ToxFactor("storage_tests", splits=2),
            ToxFactor("storage_tests_sqlalchemy_1_3", splits=2),
            ToxFactor("storage_tests_sqlalchemy_1_4", splits=2),
            ToxFactor("utils_tests"),
            ToxFactor("type_signature_tests"),
        ]
        + tox_factors_for_folder("execution_tests"),
        unsupported_python_versions=_unsupported_dagster_python_versions,
    ),
    PackageSpec(
        "python_modules/dagster-graphql",
        pytest_extra_cmds=dagster_graphql_extra_cmds,
        pytest_tox_factors=[
            ToxFactor("not_graphql_context_test_suite", splits=2),
            ToxFactor("sqlite_instance_multi_location"),
            ToxFactor("sqlite_instance_managed_grpc_env", splits=2),
            ToxFactor("sqlite_instance_deployed_grpc_env", splits=2),
            ToxFactor("sqlite_instance_code_server_cli_grpc_env", splits=2),
            ToxFactor("graphql_python_client"),
            ToxFactor("postgres-graphql_context_variants"),
            ToxFactor("postgres-instance_multi_location"),
            ToxFactor("postgres-instance_managed_grpc_env", splits=2),
            ToxFactor("postgres-instance_deployed_grpc_env", splits=2),
        ],
        unsupported_python_versions=(
            lambda tox_factor: (
                [AvailablePythonVersion.V3_11]
                if (
                    tox_factor
                    and tox_factor.factor
                    in {
                        # test suites particularly likely to crash and/or hang
                        # due to https://github.com/grpc/grpc/issues/31885
                        "sqlite_instance_managed_grpc_env",
                        "sqlite_instance_deployed_grpc_env",
                        "sqlite_instance_code_server_cli_grpc_env",
                        "sqlite_instance_multi_location",
                        "postgres-instance_multi_location",
                        "postgres-instance_managed_grpc_env",
                        "postgres-instance_deployed_grpc_env",
                    }
                )
                else []
            )
        ),
        timeout_in_minutes=30,
    ),
    PackageSpec(
        "python_modules/dagster-test",
        unsupported_python_versions=[
            # dagster-airflow
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-dbt",
        pytest_tox_factors=[
            ToxFactor(f"{deps_factor}-{command_factor}", splits=3)
            for deps_factor in ["dbt17", "dbt18", "dbt19", "dbt110"]
            for command_factor in ["cloud", "core-main", "core-derived-metadata"]
        ],
        # dbt-core 1.7's protobuf<5 constraint conflicts with the grpc requirement for Python 3.13
        unsupported_python_versions=(
            lambda tox_factor: [AvailablePythonVersion.V3_13]
            if tox_factor and tox_factor.factor.startswith("dbt17")
            else []
        ),
    ),
    PackageSpec(
        "python_modules/libraries/dagster-dbt/",
        skip_if=skip_if_not_dagster_dbt_commit,
        name="dagster-dbt-fusion",
        pytest_tox_factors=[ToxFactor("dbtfusion-snowflake")],
        env_vars=[
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_BUILDKITE_PASSWORD",
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-snowflake",
        env_vars=[
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_BUILDKITE_PASSWORD",
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-airlift",
        unsupported_python_versions=[
            # airflow
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ],
        env_vars=[
            "AIRLIFT_MWAA_TEST_ENV_NAME",
            "AIRLIFT_MWAA_TEST_PROFILE",
            "AIRLIFT_MWAA_TEST_REGION",
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-airbyte",
        pytest_tox_factors=[ToxFactor("unit"), ToxFactor("integration")],
    ),
    # PackageSpec(
    #     "python_modules/libraries/dagster-airflow",
    #     # omit python 3.10 until we add support
    #     unsupported_python_versions=[
    #         AvailablePythonVersion.V3_10,
    #         AvailablePythonVersion.V3_11,
    #         AvailablePythonVersion.V3_12,
    #         AvailablePythonVersion.V3_13,
    #     ],
    #     env_vars=[
    #         "AIRFLOW_HOME",
    #         "AWS_ACCOUNT_ID",
    #         "AWS_ACCESS_KEY_ID",
    #         "AWS_SECRET_ACCESS_KEY",
    #         "BUILDKITE_SECRETS_BUCKET",
    #         "GOOGLE_APPLICATION_CREDENTIALS",
    #     ],
    #     pytest_extra_cmds=airflow_extra_cmds,
    #     pytest_tox_factors=[
    #         ToxFactor("default-airflow2"),
    #         ToxFactor("localdb-airflow2"),
    #         ToxFactor("persistentdb-airflow2"),
    #     ],
    # ),
    PackageSpec(
        "python_modules/libraries/dagster-dg-cli",
        pytest_tox_factors=[
            ToxFactor("general", splits=3),
            ToxFactor("docs"),
            ToxFactor("plus"),
        ],
        env_vars=["SHELL"],
        always_run_if=has_dg_or_component_integration_changes,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-dg-cli",
        name="dagster-dg-cli-mcp",
        pytest_tox_factors=[ToxFactor("mcp")],
        unsupported_python_versions=[
            AvailablePythonVersion.V3_9,
        ],
        always_run_if=has_dg_or_component_integration_changes,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-aws",
        env_vars=["AWS_DEFAULT_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-azure",
        env_vars=["AZURE_STORAGE_ACCOUNT_KEY"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-celery",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        pytest_extra_cmds=celery_extra_cmds,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-celery-docker",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        pytest_extra_cmds=celery_extra_cmds,
        pytest_step_dependencies=test_project_depends_fn,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-dask",
        env_vars=["AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION"],
        unsupported_python_versions=[
            # dask
            AvailablePythonVersion.V3_9,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-databricks",
    ),
    PackageSpec(
        "python_modules/libraries/dagster-docker",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        pytest_extra_cmds=docker_extra_cmds,
        pytest_step_dependencies=test_project_depends_fn,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-duckdb",
        unsupported_python_versions=[
            # duckdb
            AvailablePythonVersion.V3_12,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-duckdb-pandas",
        unsupported_python_versions=[
            # duckdb
            AvailablePythonVersion.V3_12,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-duckdb-polars",
        unsupported_python_versions=[
            # duckdb
            AvailablePythonVersion.V3_12,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-duckdb-pyspark",
        unsupported_python_versions=[
            # duckdb
            AvailablePythonVersion.V3_12,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-pandas",
        unsupported_python_versions=[
            AvailablePythonVersion.V3_12,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-gcp",
        env_vars=[
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GCP_PROJECT_ID",
        ],
        pytest_extra_cmds=gcp_creds_extra_cmds,
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-gcp-pandas",
        env_vars=[
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GCP_PROJECT_ID",
        ],
        pytest_extra_cmds=gcp_creds_extra_cmds,
        retries=2,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-gcp-pyspark",
        env_vars=[
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GCP_PROJECT_ID",
        ],
        pytest_extra_cmds=gcp_creds_extra_cmds,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-ge",
        unsupported_python_versions=[
            AvailablePythonVersion.V3_9,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-k8s",
        env_vars=[
            "AWS_ACCOUNT_ID",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
        ],
        pytest_tox_factors=[
            ToxFactor("default"),
            ToxFactor("old_kubernetes"),
        ],
        pytest_extra_cmds=k8s_extra_cmds,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-mlflow",
    ),
    PackageSpec(
        "python_modules/libraries/dagster-mysql",
        pytest_extra_cmds=mysql_extra_cmds,
        pytest_tox_factors=[
            ToxFactor("storage_tests", splits=2),
            ToxFactor("storage_tests_sqlalchemy_1_3", splits=2),
        ],
        always_run_if=has_storage_test_fixture_changes,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-snowflake-pandas",
        env_vars=["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_BUILDKITE_PASSWORD"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-snowflake-pyspark",
        env_vars=["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_BUILDKITE_PASSWORD"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-snowflake-polars",
        env_vars=["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_BUILDKITE_PASSWORD"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-postgres",
        pytest_tox_factors=[
            ToxFactor("storage_tests"),
            ToxFactor("storage_tests_sqlalchemy_1_3"),
        ],
        always_run_if=has_storage_test_fixture_changes,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-twilio",
        env_vars=["TWILIO_TEST_ACCOUNT_SID", "TWILIO_TEST_AUTH_TOKEN"],
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-wandb",
        unsupported_python_versions=[
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagstermill",
        pytest_tox_factors=[ToxFactor("papermill1", splits=2), ToxFactor("papermill2", splits=2)],
        retries=2,  # Workaround for flaky kernel issues
        unsupported_python_versions=(
            lambda tox_factor: (
                [AvailablePythonVersion.V3_12, AvailablePythonVersion.V3_13]
                if (tox_factor and tox_factor.factor == "papermill1")
                else []
            )
        ),
    ),
    PackageSpec(
        "python_modules/libraries/dagster-airlift/perf-harness",
        always_run_if=has_dagster_airlift_changes,
        unsupported_python_versions=[
            # airflow
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-airlift/kitchen-sink",
        always_run_if=has_dagster_airlift_changes,
        unsupported_python_versions=[
            # airflow
            AvailablePythonVersion.V3_12,
            AvailablePythonVersion.V3_13,
        ],
        queue=BuildkiteQueue.DOCKER,
        splits=2,
    ),
    # Runs against live dbt cloud instance, we only want to run on commits and on the
    # nightly build
    PackageSpec(
        "python_modules/libraries/dagster-dbt/kitchen-sink",
        skip_if=skip_if_not_dagster_dbt_cloud_commit,
        name="dagster-dbt-cloud-live",
        env_vars=[
            "KS_DBT_CLOUD_ACCOUNT_ID",
            "KS_DBT_CLOUD_ACCESS_URL",
            "KS_DBT_CLOUD_TOKEN",
            "KS_DBT_CLOUD_PROJECT_ID",
            "KS_DBT_CLOUD_ENVIRONMENT_ID",
        ],
    ),
    PackageSpec(
        ".buildkite/dagster-buildkite",
        run_pytest=False,
    ),
]
