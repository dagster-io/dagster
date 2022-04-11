import os
import sys

import pytest

from dagster.core.test_utils import create_test_daemon_workspace, instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.core.workspace.load_target import ModuleTarget


@pytest.fixture(name="instance_session_scoped", scope="session")
def instance_session_scoped_fixture():
    with instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster.core.test_utils", "class": "MockedRunLauncher"}
        }
    ) as instance:
        yield instance


@pytest.fixture(name="instance", scope="function")
def instance_fixture(instance_session_scoped):
    instance_session_scoped.wipe()
    instance_session_scoped.wipe_all_schedules()
    yield instance_session_scoped


def workspace_load_target(attribute="the_repo"):
    return ModuleTarget(
        module_name="dagster_tests.scheduler_tests.test_scheduler_run",
        attribute=attribute,
        working_directory=os.path.dirname(__file__),
        location_name="test_location",
    )


@pytest.fixture(name="workspace", scope="session")
def workspace_fixture(instance_session_scoped):  # pylint: disable=unused-argument
    with create_test_daemon_workspace(workspace_load_target=workspace_load_target()) as workspace:
        yield workspace


@pytest.fixture(name="external_repo", scope="session")
def external_repo_fixture(workspace):  # pylint: disable=unused-argument
    return next(
        iter(workspace.get_workspace_snapshot().values())
    ).repository_location.get_repository("the_repo")


def loadable_target_origin():
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.scheduler_tests.test_scheduler_run",
        working_directory=os.getcwd(),
        attribute="the_repo",
    )
