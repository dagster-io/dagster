import tempfile

import dagster as dg
import pytest
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget


@pytest.fixture
def workspace(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=dg.file_relative_path(__file__, "test_op_concurrency.py"),
            attribute="concurrency_repo",
            working_directory=None,
            location_name="test",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@pytest.fixture
def instance():
    # ignore_cleanup_errors=True: multiprocess executor subprocesses can still be
    # flushing files into temp_dir when this fixture tears down, racing the rmtree
    # and surfacing as a spurious OSError(ENOTEMPTY) at teardown.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        with dg.instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster._utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir, "sleep_interval": 0.01},
                },
                "concurrency": {
                    "pools": {"granularity": "op"},
                },
            }
        ) as _instance:
            yield _instance
