import os
import sys

import pytest

from dagster._core.test_utils import create_test_daemon_workspace, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.load_target import ModuleTarget


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture():
    with instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"}
        }
    ) as instance:
        yield instance


@pytest.fixture(name="instance", scope="function")
def instance_fixture(instance_module_scoped):
    instance_module_scoped.wipe()
    instance_module_scoped.wipe_all_schedules()
    yield instance_module_scoped


def workspace_load_target(attribute="the_repo"):
    return ModuleTarget(
        module_name="dagster_tests.daemon_sensor_tests.test_sensor_run",
        attribute=attribute,
        working_directory=os.path.dirname(__file__),
        location_name="test_location",
    )


@pytest.fixture(name="workspace", scope="module")
def workspace_fixture(instance_module_scoped):  # pylint: disable=unused-argument
    with create_test_daemon_workspace(
        workspace_load_target=workspace_load_target(), instance=instance_module_scoped
    ) as workspace:
        yield workspace


@pytest.fixture(name="external_repo", scope="module")
def external_repo_fixture(workspace):  # pylint: disable=unused-argument
    return next(
        iter(workspace.get_workspace_snapshot().values())
    ).repository_location.get_repository("the_repo")


def loadable_target_origin():
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.daemon_sensor_tests.test_sensor_run",
        working_directory=os.getcwd(),
        attribute="the_repo",
    )
