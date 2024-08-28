import tempfile

import pytest
from dagster._core.test_utils import create_test_daemon_workspace_context, instance_for_test
from dagster._core.workspace.load_target import EmptyWorkspaceTarget

from auto_run_reexecution_tests.utils import workspace_load_target


@pytest.fixture
def instance():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "run_coordinator": {
                    "module": "dagster.core.test_utils",
                    "class": "MockedRunCoordinator",
                },
                "event_log_storage": {
                    "module": "dagster._core.storage.event_log",
                    "class": "ConsolidatedSqliteEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
                "run_retries": {"enabled": True},
            },
            temp_dir=temp_dir,
        ) as instance:
            yield instance


@pytest.fixture
def instance_no_retry_on_asset_or_op_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "run_coordinator": {
                    "module": "dagster.core.test_utils",
                    "class": "MockedRunCoordinator",
                },
                "event_log_storage": {
                    "module": "dagster._core.storage.event_log",
                    "class": "ConsolidatedSqliteEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
                "run_retries": {"enabled": True, "retry_on_asset_or_op_failure": False},
            },
            temp_dir=temp_dir,
        ) as instance:
            yield instance


@pytest.fixture
def empty_workspace_context(instance):
    with create_test_daemon_workspace_context(
        workspace_load_target=EmptyWorkspaceTarget(), instance=instance
    ) as workspace_context:
        yield workspace_context


@pytest.fixture
def workspace_context(instance):
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target(), instance=instance
    ) as workspace:
        yield workspace
