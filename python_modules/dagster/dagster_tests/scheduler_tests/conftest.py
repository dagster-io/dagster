import os
import sys
from typing import Iterator, Optional

import pytest
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.test_utils import (
    SingleThreadPoolExecutor,
    create_test_daemon_workspace_context,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import ModuleTarget


@pytest.fixture(params=["synchronous", "threadpool"])
def submit_executor(request):
    if request.param == "synchronous":
        yield None
    elif request.param == "threadpool":
        with SingleThreadPoolExecutor() as executor:
            yield executor


@pytest.fixture(name="instance_session_scoped", scope="session")
def instance_session_scoped_fixture() -> Iterator[DagsterInstance]:
    with instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"}
        }
    ) as instance:
        yield instance


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture(
    instance_session_scoped: DagsterInstance,
) -> Iterator[DagsterInstance]:
    instance_session_scoped.wipe()
    instance_session_scoped.wipe_all_schedules()
    yield instance_session_scoped


@pytest.fixture(name="instance", scope="function")
def instance_fixture(instance_session_scoped: DagsterInstance) -> Iterator[DagsterInstance]:
    instance_session_scoped.wipe()
    instance_session_scoped.wipe_all_schedules()
    yield instance_session_scoped


def workspace_load_target(
    module: Optional[str] = "test_scheduler_run", attribute: Optional[str] = "the_repo"
) -> ModuleTarget:
    return ModuleTarget(
        module_name=f"dagster_tests.scheduler_tests.{module}",
        attribute=attribute,
        working_directory=os.path.join(os.path.dirname(__file__), "..", ".."),
        location_name="test_location",
    )


@pytest.fixture(name="workspace_context", scope="session")
def workspace_fixture(
    instance_session_scoped: DagsterInstance,
) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target(), instance=instance_session_scoped
    ) as workspace:
        yield workspace


@pytest.fixture(name="external_repo", scope="session")
def external_repo_fixture(workspace_context: WorkspaceProcessContext) -> RemoteRepository:
    return next(
        iter(workspace_context.create_request_context().get_code_location_entries().values())
    ).code_location.get_repository(  # type: ignore  # (possible none)
        "the_repo"
    )


def loadable_target_origin() -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.scheduler_tests.test_scheduler_run",
        working_directory=os.getcwd(),
        attribute="the_repo",
    )


@pytest.fixture(name="workspace_one", scope="session")
def workspace_one_fixture(
    instance_session_scoped: DagsterInstance,
) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target("simple_repo_one"),
        instance=instance_session_scoped,
    ) as workspace:
        yield workspace


@pytest.fixture(name="workspace_two", scope="session")
def workspace_two_fixture(
    instance_session_scoped: DagsterInstance,
) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target("simple_repo_two"),
        instance=instance_session_scoped,
    ) as workspace:
        yield workspace
