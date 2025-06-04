import pytest
from dagster._core.launcher.base import DagsterRun, LaunchRunContext


@pytest.fixture
def stub_launch_context() -> LaunchRunContext:
    return LaunchRunContext(dagster_run=DagsterRun(job_name="job_name"), workspace=None)
