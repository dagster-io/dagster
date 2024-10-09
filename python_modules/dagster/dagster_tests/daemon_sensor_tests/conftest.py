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
    load_external_repo,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import ModuleTarget


@pytest.fixture(params=["synchronous", "threadpool"])
def executor(request):
    if request.param == "synchronous":
        yield None
    elif request.param == "threadpool":
        with SingleThreadPoolExecutor() as executor:
            yield executor


@pytest.fixture(params=["synchronous", "threadpool"])
def submit_executor(request):
    if request.param == "synchronous":
        yield None
    elif request.param == "threadpool":
        with SingleThreadPoolExecutor() as executor:
            yield executor


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture() -> Iterator[DagsterInstance]:
    with instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"}
        }
    ) as instance:
        yield instance


@pytest.fixture(name="instance", scope="function")
def instance_fixture(instance_module_scoped: DagsterInstance) -> Iterator[DagsterInstance]:
    instance_module_scoped.wipe()
    instance_module_scoped.wipe_all_schedules()
    yield instance_module_scoped


def create_workspace_load_target(attribute: Optional[str] = "the_repo") -> ModuleTarget:
    return ModuleTarget(
        module_name="dagster_tests.daemon_sensor_tests.test_sensor_run",
        attribute=attribute,
        working_directory=os.path.join(os.path.dirname(__file__), "..", ".."),
        location_name="test_location",
    )


@pytest.fixture(name="workspace_context", scope="module")
def workspace_fixture(instance_module_scoped: DagsterInstance) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=create_workspace_load_target(),
        instance=instance_module_scoped,
    ) as workspace:
        yield workspace


@pytest.fixture(name="external_repo", scope="module")
def external_repo_fixture(workspace_context: WorkspaceProcessContext) -> RemoteRepository:
    return load_external_repo(workspace_context, "the_repo")


def loadable_target_origin() -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.daemon_sensor_tests.test_sensor_run",
        working_directory=os.getcwd(),
        attribute="the_repo",
    )
