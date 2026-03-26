import tempfile
from collections.abc import Iterator

import pytest
from dagster import file_relative_path
from dagster._core.instance_for_test import cleanup_test_instance
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster_graphql.test.utils import define_out_of_process_workspace


def _yield_graphql_context(
    workspace: WorkspaceProcessContext,
) -> Iterator[WorkspaceRequestContext]:
    """Wipe instance state, yield a fresh request context, then clean up launched runs."""
    instance = workspace.instance
    instance.wipe()
    instance.wipe_all_schedules()
    with workspace.create_request_context() as request_context:
        yield request_context
    cleanup_test_instance(instance)


@pytest.fixture(scope="module")
def _graphql_workspace():
    """Module-scoped fixture that creates the expensive resources once: a temp directory,
    DagsterInstance, and WorkspaceProcessContext (which launches a gRPC subprocess to load
    the test repository). Individual tests get a fresh WorkspaceRequestContext via the
    function-scoped graphql_context fixture.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            temp_dir=temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.utils.test",
                    "class": "FilesystemTestScheduler",
                    "config": {"base_dir": temp_dir},
                },
            },
            synchronous_run_coordinator=True,
        ) as instance:
            with define_out_of_process_workspace(
                file_relative_path(__file__, "repo.py"), "test_repo", instance
            ) as workspace:
                yield workspace


@pytest.fixture(scope="function")
def graphql_context(_graphql_workspace):
    yield from _yield_graphql_context(_graphql_workspace)


@pytest.fixture(scope="module")
def _definitions_graphql_workspace():
    """Module-scoped fixture for the definitions-based test repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            temp_dir=temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.utils.test",
                    "class": "FilesystemTestScheduler",
                    "config": {"base_dir": temp_dir},
                },
            },
        ) as instance:
            with define_out_of_process_workspace(
                file_relative_path(__file__, "repo_definitions.py"), "defs", instance
            ) as workspace:
                yield workspace


@pytest.fixture(scope="function")
def definitions_graphql_context(_definitions_graphql_workspace):
    yield from _yield_graphql_context(_definitions_graphql_workspace)
