import sys
import tempfile
from abc import ABC, abstractmethod
from contextlib import contextmanager
from unittest.mock import patch

import dagster._check as check
import pytest
from dagster import file_relative_path
from dagster._core.instance import DagsterInstance, InstanceType
from dagster._core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.storage.event_log.sqlite import ConsolidatedSqliteEventLogStorage
from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs import InMemoryRunStorage
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import (
    GrpcServerTarget,
    ModuleTarget,
    PythonFileTarget,
    WorkspaceFileTarget,
)
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import GrpcServerProcess, wait_for_grpc_server
from dagster._serdes.ipc import open_ipc_subprocess
from dagster._utils import safe_tempfile_path
from dagster._utils.merger import merge_dicts
from dagster._utils.test import FilesystemTestScheduler
from dagster._utils.test.postgres_instance import TestPostgresInstance
from dagster_graphql import DagsterGraphQLClient
from dagster_graphql.test.utils import execute_dagster_graphql
from graphql import DocumentNode, print_ast


def get_main_loadable_target_origin():
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=file_relative_path(__file__, "repo.py"),
        attribute="test_repo",
    )


@contextmanager
def graphql_postgres_instance(overrides=None):
    with tempfile.TemporaryDirectory() as temp_dir:
        with TestPostgresInstance.docker_service_up_or_skip(
            file_relative_path(__file__, "docker-compose.yml"),
            "test-postgres-db-graphql",
        ) as pg_conn_string:
            TestPostgresInstance.clean_run_storage(pg_conn_string)
            TestPostgresInstance.clean_event_log_storage(pg_conn_string)
            TestPostgresInstance.clean_schedule_storage(pg_conn_string)
            with instance_for_test(
                temp_dir=temp_dir,
                overrides=merge_dicts(
                    {
                        "run_storage": {
                            "module": "dagster_postgres.run_storage.run_storage",
                            "class": "PostgresRunStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                        "event_log_storage": {
                            "module": "dagster_postgres.event_log.event_log",
                            "class": "PostgresEventLogStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                        "schedule_storage": {
                            "module": "dagster_postgres.schedule_storage.schedule_storage",
                            "class": "PostgresScheduleStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                        "scheduler": {
                            "module": "dagster.utils.test",
                            "class": "FilesystemTestScheduler",
                            "config": {"base_dir": temp_dir},
                        },
                    },
                    overrides if overrides else {},
                ),
            ) as instance:
                yield instance


class MarkedManager:
    """MarkedManagers are passed to GraphQLContextVariants. They contain
    a contextmanager function "manager_fn" that yield the relevant
    instance, and it includes marks that will be applied to any
    context-variant-driven test case that includes this MarkedManager.

    See InstanceManagers for an example construction.

    See GraphQLContextVariant for further information
    """

    def __init__(self, manager_fn, marks):
        self.manager_fn = check.callable_param(manager_fn, "manager_fn")
        self.marks = check.list_param(marks, "marks")


class InstanceManagers:
    @staticmethod
    def non_launchable_sqlite_instance():
        @contextmanager
        def _non_launchable_sqlite_instance():
            with tempfile.TemporaryDirectory() as temp_dir:
                with instance_for_test(
                    temp_dir=temp_dir,
                    overrides={
                        "run_coordinator": {
                            "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                            "class": "ImmediatelyLaunchRunCoordinator",
                        },
                        "scheduler": {
                            "module": "dagster.utils.test",
                            "class": "FilesystemTestScheduler",
                            "config": {"base_dir": temp_dir},
                        },
                        "run_launcher": {
                            "module": "dagster._core.test_utils",
                            "class": "ExplodingRunLauncher",
                        },
                    },
                ) as instance:
                    yield instance

        return MarkedManager(
            _non_launchable_sqlite_instance, [Marks.sqlite_instance, Marks.non_launchable]
        )

    @staticmethod
    def non_launchable_postgres_instance():
        @contextmanager
        def _non_launchable_postgres_instance():
            with graphql_postgres_instance(
                overrides={
                    "run_coordinator": {
                        "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                        "class": "ImmediatelyLaunchRunCoordinator",
                    },
                    "run_launcher": {
                        "module": "dagster._core.test_utils",
                        "class": "ExplodingRunLauncher",
                    },
                }
            ) as instance:
                yield instance

        return MarkedManager(
            _non_launchable_postgres_instance,
            [Marks.postgres_instance, Marks.non_launchable],
        )

    @staticmethod
    def sqlite_instance_with_sync_run_launcher():
        @contextmanager
        def _sqlite_instance():
            with tempfile.TemporaryDirectory() as temp_dir:
                with instance_for_test(
                    temp_dir=temp_dir,
                    overrides={
                        "scheduler": {
                            "module": "dagster.utils.test",
                            "class": "FilesystemTestScheduler",
                            "config": {"base_dir": temp_dir},
                        },
                        "run_launcher": {
                            "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                            "class": "SyncInMemoryRunLauncher",
                        },
                    },
                ) as instance:
                    yield instance

        return MarkedManager(_sqlite_instance, [Marks.sqlite_instance, Marks.sync_run_launcher])

    # Runs launched with this instance won't actually execute since the graphql test suite
    # doesn't run the daemon process that launches queued runs
    @staticmethod
    def sqlite_instance_with_queued_run_coordinator():
        @contextmanager
        def _sqlite_instance():
            with tempfile.TemporaryDirectory() as temp_dir:
                with instance_for_test(
                    temp_dir=temp_dir,
                    overrides={
                        "scheduler": {
                            "module": "dagster.utils.test",
                            "class": "FilesystemTestScheduler",
                            "config": {"base_dir": temp_dir},
                        },
                        "run_coordinator": {
                            "module": "dagster._core.run_coordinator.queued_run_coordinator",
                            "class": "QueuedRunCoordinator",
                        },
                    },
                ) as instance:
                    yield instance

        return MarkedManager(
            _sqlite_instance, [Marks.sqlite_instance, Marks.queued_run_coordinator]
        )

    @staticmethod
    def sqlite_instance_with_default_run_launcher():
        @contextmanager
        def _sqlite_instance_with_default_hijack():
            with tempfile.TemporaryDirectory() as temp_dir:
                with instance_for_test(
                    temp_dir=temp_dir,
                    overrides={
                        "run_coordinator": {
                            "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                            "class": "ImmediatelyLaunchRunCoordinator",
                        },
                        "scheduler": {
                            "module": "dagster.utils.test",
                            "class": "FilesystemTestScheduler",
                            "config": {"base_dir": temp_dir},
                        },
                    },
                ) as instance:
                    yield instance

        return MarkedManager(
            _sqlite_instance_with_default_hijack,
            [Marks.sqlite_instance, Marks.default_run_launcher],
        )

    @staticmethod
    def postgres_instance_with_sync_run_launcher():
        @contextmanager
        def _postgres_instance():
            with graphql_postgres_instance(
                overrides={
                    "run_coordinator": {
                        "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                        "class": "ImmediatelyLaunchRunCoordinator",
                    },
                    "run_launcher": {
                        "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                        "class": "SyncInMemoryRunLauncher",
                    },
                }
            ) as instance:
                yield instance

        return MarkedManager(
            _postgres_instance,
            [Marks.postgres_instance, Marks.sync_run_launcher],
        )

    @staticmethod
    def postgres_instance_with_default_run_launcher():
        @contextmanager
        def _postgres_instance_with_default_hijack():
            with graphql_postgres_instance(
                overrides={
                    "run_coordinator": {
                        "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                        "class": "ImmediatelyLaunchRunCoordinator",
                    },
                }
            ) as instance:
                yield instance

        return MarkedManager(
            _postgres_instance_with_default_hijack,
            [Marks.postgres_instance, Marks.default_run_launcher],
        )

    @staticmethod
    def consolidated_sqlite_instance():
        @contextmanager
        def _sqlite_asset_instance():
            with tempfile.TemporaryDirectory() as temp_dir:
                instance = DagsterInstance(
                    instance_type=InstanceType.EPHEMERAL,
                    local_artifact_storage=LocalArtifactStorage(temp_dir),
                    run_storage=InMemoryRunStorage(),
                    event_storage=ConsolidatedSqliteEventLogStorage(temp_dir),
                    compute_log_manager=LocalComputeLogManager(temp_dir),
                    run_coordinator=DefaultRunCoordinator(),
                    run_launcher=SyncInMemoryRunLauncher(),
                    scheduler=FilesystemTestScheduler(temp_dir),
                )
                yield instance

        return MarkedManager(_sqlite_asset_instance, [Marks.asset_aware_instance])

    @staticmethod
    def default_concurrency_sqlite_instance():
        @contextmanager
        def _sqlite_with_default_concurrency_instance():
            with tempfile.TemporaryDirectory() as temp_dir:
                with instance_for_test(
                    temp_dir=temp_dir,
                    overrides={
                        "scheduler": {
                            "module": "dagster.utils.test",
                            "class": "FilesystemTestScheduler",
                            "config": {"base_dir": temp_dir},
                        },
                        "run_coordinator": {
                            "module": "dagster._core.run_coordinator.queued_run_coordinator",
                            "class": "QueuedRunCoordinator",
                        },
                        "concurrency": {
                            "default_op_concurrency_limit": 1,
                        },
                    },
                ) as instance:
                    yield instance

        return MarkedManager(
            _sqlite_with_default_concurrency_instance,
            [Marks.sqlite_instance, Marks.queued_run_coordinator],
        )


class EnvironmentManagers:
    @staticmethod
    def managed_grpc(target=None, location_name="test_location"):
        @contextmanager
        def _mgr_fn(instance, read_only):
            """Relies on webserver to load the code location in a subprocess and manage its lifecyle."""
            loadable_target_origin = (
                target if target is not None else get_main_loadable_target_origin()
            )
            with WorkspaceProcessContext(
                instance,
                (
                    PythonFileTarget(
                        python_file=loadable_target_origin.python_file,
                        attribute=loadable_target_origin.attribute,
                        working_directory=loadable_target_origin.working_directory,
                        location_name=location_name,
                    )
                    if loadable_target_origin.python_file
                    else ModuleTarget(
                        module_name=loadable_target_origin.module_name,  # pyright: ignore[reportArgumentType]
                        attribute=loadable_target_origin.attribute,
                        working_directory=loadable_target_origin.working_directory,
                        location_name=location_name,
                    )
                ),
                version="",
                read_only=read_only,
            ) as workspace_process_context:
                yield workspace_process_context

        return MarkedManager(_mgr_fn, [Marks.managed_grpc_env])

    @staticmethod
    def deployed_grpc(target=None, location_name="test_location"):
        """Launches a code server in a "dagster api grpc" subprocess."""

        @contextmanager
        def _mgr_fn(instance, read_only):
            with GrpcServerProcess(
                instance_ref=instance.get_ref(),
                location_name=location_name,
                loadable_target_origin=(
                    target if target is not None else get_main_loadable_target_origin()
                ),
                wait_on_exit=True,
            ) as server_process:
                api_client = server_process.create_client()
                with WorkspaceProcessContext(
                    instance,
                    GrpcServerTarget(
                        port=api_client.port,
                        socket=api_client.socket,
                        host=api_client.host,  # pyright: ignore[reportArgumentType]
                        location_name=location_name,
                    ),
                    version="",
                    read_only=read_only,
                ) as workspace:
                    yield workspace

        return MarkedManager(_mgr_fn, [Marks.deployed_grpc_env])

    @staticmethod
    def code_server_cli_grpc(target=None, location_name="test_location"):
        """Launches a code server in a "dagster code-server start" subprocess (which will
        in turn open up a `dagster api grpc` subprocess that actually loads the code location).
        """

        @contextmanager
        def _mgr_fn(instance, read_only):
            loadable_target_origin = target or get_main_loadable_target_origin()
            with safe_tempfile_path() as socket:
                subprocess_args = [  # pyright: ignore[reportOperatorIssue]
                    "dagster",
                    "code-server",
                    "start",
                    "--socket",
                    socket,
                ] + loadable_target_origin.get_cli_args()

                server_process = open_ipc_subprocess(subprocess_args)

                client = DagsterGrpcClient(port=None, socket=socket, host="localhost")

                try:
                    wait_for_grpc_server(server_process, client, subprocess_args)
                    with WorkspaceProcessContext(
                        instance,
                        GrpcServerTarget(
                            port=None,
                            socket=socket,
                            host="localhost",
                            location_name=location_name,
                        ),
                        version="",
                        read_only=read_only,
                    ) as workspace:
                        yield workspace
                finally:
                    client.shutdown_server()
                    server_process.wait(timeout=30)

        return MarkedManager(_mgr_fn, [Marks.code_server_cli_grpc_env])

    @staticmethod
    def multi_location():
        @contextmanager
        def _mgr_fn(instance, read_only):
            """Goes out of process but same process as host process."""
            with WorkspaceProcessContext(
                instance,
                WorkspaceFileTarget(paths=[file_relative_path(__file__, "multi_location.yaml")]),
                version="",
                read_only=read_only,
            ) as workspace:
                yield workspace

        return MarkedManager(_mgr_fn, [Marks.multi_location])

    @staticmethod
    def lazy_repository():
        @contextmanager
        def _mgr_fn(instance, read_only):
            """Goes out of process but same process as host process."""
            with WorkspaceProcessContext(
                instance,
                PythonFileTarget(
                    python_file=file_relative_path(__file__, "repo.py"),
                    attribute="test_dict_repo",
                    working_directory=None,
                    location_name="test_location",
                ),
                version="",
                read_only=read_only,
            ) as workspace:
                yield workspace

        return MarkedManager(_mgr_fn, [Marks.lazy_repository])


class Marks:
    # Instance type makes
    sqlite_instance = pytest.mark.sqlite_instance
    postgres_instance = pytest.mark.postgres_instance

    # Run launcher variants
    sync_run_launcher = pytest.mark.sync_run_launcher
    default_run_launcher = pytest.mark.default_run_launcher
    queued_run_coordinator = pytest.mark.queued_run_coordinator
    non_launchable = pytest.mark.non_launchable

    # Code location marks
    multi_location = pytest.mark.multi_location
    managed_grpc_env = pytest.mark.managed_grpc_env
    deployed_grpc_env = pytest.mark.deployed_grpc_env
    code_server_cli_grpc_env = pytest.mark.code_server_cli_grpc_env

    lazy_repository = pytest.mark.lazy_repository

    # Asset-aware sqlite variants
    asset_aware_instance = pytest.mark.asset_aware_instance

    # Backfill daemon variants
    backfill_daemon = pytest.mark.backfill_daemon

    # Readonly context variant
    read_only = pytest.mark.read_only

    # Common mark to all test suite tests
    graphql_context_test_suite = pytest.mark.graphql_context_test_suite


def none_manager():
    @contextmanager
    def _yield_none(*_args, **_kwargs):
        yield None

    return MarkedManager(_yield_none, [])


class GraphQLContextVariant:
    """An instance of this class represents a context variant that will be run
    against *every* method in the test class, defined as a class
    created by inheriting from make_graphql_context_test_suite.

    It comes with a number of static methods with prebuilt context variants.
    e.g. in_memory_in_process_start

    One can also make bespoke context variants, provided you configure it properly
    with MarkedMembers that produce its members.

    Args:
    marked_instance_mgr (MarkedManager): The manager_fn
    within it must be a contextmanager that takes zero arguments and yields
    a DagsterInstance

    See InstanceManagers for examples

    marked_environment_mgr (MarkedManager): The manager_fn with in
    must be a contextmanager takes a default ReconstructableRepo and
    yields a list of RepositoryLocation.

    See EnvironmentManagers for examples

    test_id [Optional] (str): This assigns a test_id to test parameterized with this
    variant. This is highly convenient for running a particular variant across
    the entire test suite, without running all the other variants.

    e.g.
    pytest python_modules/dagster-graphql/dagster_graphql_tests/ -s -k in_memory_in_process_start

    Will run all tests that use the in_memory_in_process_start, which will get a lot
    of code coverage while being very fast to run.

    All tests managed by this system are marked with "graphql_context_test_suite".
    """

    def __init__(self, marked_instance_mgr, marked_environment_mgr, read_only=False, test_id=None):
        self.marked_instance_mgr = check.inst_param(
            marked_instance_mgr, "marked_instance_mgr", MarkedManager
        )
        self.marked_environment_mgr = check.inst_param(
            marked_environment_mgr, "marked_environment_mgr", MarkedManager
        )
        self.read_only = check.bool_param(read_only, "read_only")
        self.test_id = check.opt_str_param(test_id, "test_id")
        self.marks = (
            marked_instance_mgr.marks
            + marked_environment_mgr.marks
            + ([Marks.read_only] if read_only else [])
        )

    @property
    def instance_mgr(self):
        return self.marked_instance_mgr.manager_fn

    @property
    def environment_mgr(self):
        return self.marked_environment_mgr.manager_fn

    @staticmethod
    def sqlite_with_queued_run_coordinator_managed_grpc_env():
        return GraphQLContextVariant(
            InstanceManagers.sqlite_instance_with_queued_run_coordinator(),
            EnvironmentManagers.managed_grpc(),
            test_id="sqlite_with_queued_run_coordinator_managed_grpc_env",
        )

    @staticmethod
    def sqlite_with_default_run_launcher_managed_grpc_env(
        target=None, location_name="test_location"
    ):
        return GraphQLContextVariant(
            InstanceManagers.sqlite_instance_with_default_run_launcher(),
            EnvironmentManagers.managed_grpc(target, location_name),
            test_id="sqlite_with_default_run_launcher_managed_grpc_env",
        )

    @staticmethod
    def sqlite_read_only_with_default_run_launcher_managed_grpc_env():
        return GraphQLContextVariant(
            InstanceManagers.sqlite_instance_with_default_run_launcher(),
            EnvironmentManagers.managed_grpc(),
            read_only=True,
            test_id="sqlite_read_only_with_default_run_launcher_managed_grpc_env",
        )

    @staticmethod
    def sqlite_with_default_run_launcher_deployed_grpc_env(
        target=None, location_name="test_location"
    ):
        return GraphQLContextVariant(
            InstanceManagers.sqlite_instance_with_default_run_launcher(),
            EnvironmentManagers.deployed_grpc(target, location_name),
            test_id="sqlite_with_default_run_launcher_deployed_grpc_env",
        )

    @staticmethod
    def sqlite_with_default_run_launcher_code_server_cli_env(
        target=None, location_name="test_location"
    ):
        return GraphQLContextVariant(
            InstanceManagers.sqlite_instance_with_default_run_launcher(),
            EnvironmentManagers.code_server_cli_grpc(target, location_name),
            test_id="sqlite_with_default_run_launcher_code_server_cli_env",
        )

    @staticmethod
    def sqlite_with_default_concurrency_managed_grpc_env(
        target=None, location_name="test_location"
    ):
        return GraphQLContextVariant(
            InstanceManagers.default_concurrency_sqlite_instance(),
            EnvironmentManagers.managed_grpc(target, location_name),
            test_id="sqlite_with_default_concurrency_managed_grpc_env",
        )

    @staticmethod
    def postgres_with_default_run_launcher_managed_grpc_env(
        target=None, location_name="test_location"
    ):
        return GraphQLContextVariant(
            InstanceManagers.postgres_instance_with_default_run_launcher(),
            EnvironmentManagers.managed_grpc(target, location_name),
            test_id="postgres_with_default_run_launcher_managed_grpc_env",
        )

    @staticmethod
    def postgres_with_default_run_launcher_deployed_grpc_env(
        target=None, location_name="test_location"
    ):
        return GraphQLContextVariant(
            InstanceManagers.postgres_instance_with_default_run_launcher(),
            EnvironmentManagers.deployed_grpc(target, location_name),
            test_id="postgres_with_default_run_launcher_deployed_grpc_env",
        )

    @staticmethod
    def non_launchable_sqlite_instance_multi_location():
        return GraphQLContextVariant(
            InstanceManagers.non_launchable_sqlite_instance(),
            EnvironmentManagers.multi_location(),
            test_id="non_launchable_sqlite_instance_multi_location",
        )

    @staticmethod
    def non_launchable_sqlite_instance_lazy_repository():
        return GraphQLContextVariant(
            InstanceManagers.non_launchable_sqlite_instance(),
            EnvironmentManagers.lazy_repository(),
            test_id="non_launchable_sqlite_instance_lazy_repository",
        )

    @staticmethod
    def non_launchable_sqlite_instance_managed_grpc_env():
        return GraphQLContextVariant(
            InstanceManagers.non_launchable_sqlite_instance(),
            EnvironmentManagers.managed_grpc(),
            test_id="non_launchable_sqlite_instance_managed_grpc_env",
        )

    @staticmethod
    def non_launchable_sqlite_instance_deployed_grpc_env():
        return GraphQLContextVariant(
            InstanceManagers.non_launchable_sqlite_instance(),
            EnvironmentManagers.deployed_grpc(),
            test_id="non_launchable_sqlite_instance_deployed_grpc_env",
        )

    @staticmethod
    def non_launchable_postgres_instance_multi_location():
        return GraphQLContextVariant(
            InstanceManagers.non_launchable_postgres_instance(),
            EnvironmentManagers.multi_location(),
            test_id="non_launchable_postgres_instance_multi_location",
        )

    @staticmethod
    def non_launchable_postgres_instance_lazy_repository():
        return GraphQLContextVariant(
            InstanceManagers.non_launchable_postgres_instance(),
            EnvironmentManagers.lazy_repository(),
            test_id="non_launchable_postgres_instance_lazy_repository",
        )

    @staticmethod
    def non_launchable_postgres_instance_managed_grpc_env():
        return GraphQLContextVariant(
            InstanceManagers.non_launchable_postgres_instance(),
            EnvironmentManagers.managed_grpc(),
            test_id="non_launchable_postgres_instance_managed_grpc_env",
        )

    @staticmethod
    def consolidated_sqlite_instance_managed_grpc_env():
        return GraphQLContextVariant(
            InstanceManagers.consolidated_sqlite_instance(),
            EnvironmentManagers.managed_grpc(),
            test_id="asset_aware_instance_in_process_env",
        )

    @staticmethod
    def all_variants():
        """There is a test case that keeps this up-to-date. If you add a static
        method that returns a GraphQLContextVariant you have to add it to this
        list in order for tests to pass.
        """
        return [
            GraphQLContextVariant.sqlite_with_default_run_launcher_managed_grpc_env(),
            GraphQLContextVariant.sqlite_read_only_with_default_run_launcher_managed_grpc_env(),
            GraphQLContextVariant.sqlite_with_default_run_launcher_deployed_grpc_env(),
            GraphQLContextVariant.sqlite_with_default_run_launcher_code_server_cli_env(),
            GraphQLContextVariant.sqlite_with_queued_run_coordinator_managed_grpc_env(),
            GraphQLContextVariant.postgres_with_default_run_launcher_managed_grpc_env(),
            GraphQLContextVariant.postgres_with_default_run_launcher_deployed_grpc_env(),
            GraphQLContextVariant.non_launchable_sqlite_instance_multi_location(),
            GraphQLContextVariant.non_launchable_sqlite_instance_managed_grpc_env(),
            GraphQLContextVariant.non_launchable_sqlite_instance_deployed_grpc_env(),
            GraphQLContextVariant.non_launchable_sqlite_instance_lazy_repository(),
            GraphQLContextVariant.non_launchable_postgres_instance_multi_location(),
            GraphQLContextVariant.non_launchable_postgres_instance_managed_grpc_env(),
            GraphQLContextVariant.non_launchable_postgres_instance_lazy_repository(),
            GraphQLContextVariant.consolidated_sqlite_instance_managed_grpc_env(),
            GraphQLContextVariant.sqlite_with_default_concurrency_managed_grpc_env(),
        ]

    @staticmethod
    def all_executing_variants(target=None, location_name="test_location"):
        return [
            GraphQLContextVariant.sqlite_with_default_run_launcher_managed_grpc_env(
                target, location_name
            ),
            GraphQLContextVariant.sqlite_with_default_run_launcher_deployed_grpc_env(
                target, location_name
            ),
            GraphQLContextVariant.sqlite_with_default_run_launcher_code_server_cli_env(
                target, location_name
            ),
            GraphQLContextVariant.postgres_with_default_run_launcher_managed_grpc_env(
                target, location_name
            ),
            GraphQLContextVariant.postgres_with_default_run_launcher_deployed_grpc_env(
                target, location_name
            ),
        ]

    @staticmethod
    def all_readonly_variants():
        """Return all read only variants. If you try to run any mutation these will error."""
        return _variants_with_mark(GraphQLContextVariant.all_variants(), pytest.mark.read_only)

    @staticmethod
    def all_non_launchable_variants():
        """Return all non_launchable variants. If you try to start or launch these will error."""
        return _variants_with_mark(GraphQLContextVariant.all_variants(), pytest.mark.non_launchable)

    @staticmethod
    def all_multi_location_variants():
        return _variants_with_mark(GraphQLContextVariant.all_variants(), pytest.mark.multi_location)


def _variants_with_mark(variants, mark):
    def _yield_all():
        for variant in variants:
            if mark in variant.marks:
                yield variant

    return list(_yield_all())


def _variants_without_marks(variants, marks):
    def _yield_all():
        for variant in variants:
            if all(mark not in variant.marks for mark in marks):
                yield variant

    return list(_yield_all())


@contextmanager
def manage_graphql_context(context_variant):
    with context_variant.instance_mgr() as instance:
        with context_variant.environment_mgr(
            instance, context_variant.read_only
        ) as workspace_process_context:
            yield workspace_process_context


class _GraphQLContextTestSuite(ABC):
    @abstractmethod
    def yield_graphql_context(self, request):
        pass

    @contextmanager
    def graphql_context_for_request(self, request):
        check.param_invariant(
            isinstance(request.param, GraphQLContextVariant),
            "request",
            "params in fixture must be List[GraphQLContextVariant]",
        )
        with manage_graphql_context(request.param) as graphql_context:
            yield graphql_context


def graphql_context_variants_fixture(context_variants):
    check.list_param(context_variants, "context_variants", of_type=GraphQLContextVariant)

    def _wrap(fn):
        return pytest.fixture(
            name="class_scoped_graphql_context",
            scope="class",
            params=[
                pytest.param(
                    context_variant,
                    id=context_variant.test_id,
                    marks=context_variant.marks + [Marks.graphql_context_test_suite],
                )
                for context_variant in context_variants
            ],
        )(fn)

    return _wrap


def make_graphql_context_test_suite(context_variants):
    """Arguments:
        context_variants (List[GraphQLContextVariant]): List of runs to run per test in this class.

        This is the base class factory for test suites in the dagster-graphql test.

        The goal of this suite is to make it straightforward to run tests
        against multiple graphql_contexts, have a coherent lifecycle for those
        contexts.

        GraphQLContextVariant has a number of static methods to provide common run configurations
        as well as common groups of run configuration

        One can also make bespoke GraphQLContextVariants with specific implementations
        of DagsterInstance, RepositoryLocation, and so forth. See that class
        for more details.

    Example:
    class TestAThing(
        make_graphql_context_test_suite(
            context_variants=[GraphQLContextVariant.in_memory_in_process_start()]
        )
    ):
        def test_graphql_context_exists(self, graphql_context):
            assert graphql_context
    """
    check.list_param(context_variants, "context_variants", of_type=GraphQLContextVariant)

    class _SpecificTestSuiteBase(_GraphQLContextTestSuite):
        @graphql_context_variants_fixture(context_variants=context_variants)
        def yield_class_scoped_graphql_context(self, request):
            with self.graphql_context_for_request(request) as graphql_context:
                yield graphql_context

        @pytest.fixture(name="graphql_context")
        def yield_graphql_context(self, class_scoped_graphql_context):
            instance = class_scoped_graphql_context.instance
            instance.wipe()
            instance.wipe_all_schedules()
            yield class_scoped_graphql_context.create_request_context()
            # ensure that any runs launched by the test are cleaned up
            # Since launcher is lazy loaded, we don't need to do anyting if it's None
            if instance._run_launcher:  # noqa: SLF001
                instance._run_launcher.join()  # noqa: SLF001

        @pytest.fixture(name="graphql_client")
        def yield_graphql_client(self, graphql_context):
            class MockedGraphQLClient:
                def execute(self, gql_query: DocumentNode, variable_values=None):
                    return execute_dagster_graphql(
                        graphql_context,
                        print_ast(gql_query),  # convert doc back to str
                        variable_values,
                    ).data

            with patch("dagster_graphql.client.client.Client") as mock_client:
                mock_client.return_value = MockedGraphQLClient()
                yield DagsterGraphQLClient("localhost")

    return _SpecificTestSuiteBase


ReadonlyGraphQLContextTestMatrix = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_readonly_variants()
)


NonLaunchableGraphQLContextTestMatrix = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_non_launchable_variants()
)

ExecutingGraphQLContextTestMatrix = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_executing_variants()
)


all_repos_loadable_target = LoadableTargetOrigin(
    executable_path=sys.executable,
    python_file=file_relative_path(__file__, "cross_repo_asset_deps.py"),
)
AllRepositoryGraphQLContextTestMatrix = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_executing_variants(
        target=all_repos_loadable_target, location_name="cross_asset_repos"
    )
)
