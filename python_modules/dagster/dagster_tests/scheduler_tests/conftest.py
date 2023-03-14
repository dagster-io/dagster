import os
import sys
from typing import Optional

import pytest
from dagster._core.test_utils import create_test_daemon_workspace_context, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.load_target import ModuleTarget


@pytest.fixture(name="instance_session_scoped", scope="session")
def instance_session_scoped_fixture():
    with instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"}
        }
    ) as instance:
        yield instance


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture(instance_session_scoped):
    instance_session_scoped.wipe()
    instance_session_scoped.wipe_all_schedules()
    yield instance_session_scoped


@pytest.fixture(name="instance", scope="function")
def instance_fixture(instance_session_scoped):
    instance_session_scoped.wipe()
    instance_session_scoped.wipe_all_schedules()
    yield instance_session_scoped


def workspace_load_target(attribute: Optional[str] = "the_repo") -> ModuleTarget:
    return ModuleTarget(
        module_name="dagster_tests.scheduler_tests.test_scheduler_run",
        attribute=attribute,
        working_directory=os.path.dirname(__file__),
        location_name="test_location",
    )


@pytest.fixture(name="workspace_context", scope="session")
def workspace_fixture(instance_session_scoped):
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target(), instance=instance_session_scoped
    ) as workspace:
        yield workspace


@pytest.fixture(name="external_repo", scope="session")
def external_repo_fixture(workspace_context):
    return next(
        iter(workspace_context.create_request_context().get_workspace_snapshot().values())
    ).repository_location.get_repository("the_repo")


def loadable_target_origin() -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.scheduler_tests.test_scheduler_run",
        working_directory=os.getcwd(),
        attribute="the_repo",
    )
