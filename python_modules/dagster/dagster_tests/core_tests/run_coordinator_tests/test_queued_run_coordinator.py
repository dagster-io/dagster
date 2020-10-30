import contextlib

import pytest
from dagster.check import CheckError
from dagster.core.run_coordinator.queued_run_coordinator import QueuedRunCoordinator
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.utils import merge_dicts
from dagster.utils.external import external_pipeline_from_run
from dagster_tests.api_tests.utils import get_foo_pipeline_handle


@pytest.fixture()
def instance():
    overrides = {
        "run_launcher": {"module": "dagster.core.test_utils", "class": "MockedRunLauncher"}
    }
    with instance_for_test(overrides=overrides) as inst:
        yield inst


@pytest.fixture()
def coordinator(instance):  # pylint: disable=redefined-outer-name
    run_coordinator = QueuedRunCoordinator()
    run_coordinator.initialize(instance)
    yield run_coordinator


def call_submit_run(coodinator, run):  # pylint: disable=redefined-outer-name
    with external_pipeline_from_run(run) as external:
        return coodinator.submit_run(run, external)


@contextlib.contextmanager
def create_run(instance, **kwargs):  # pylint: disable=redefined-outer-name
    with get_foo_pipeline_handle() as pipeline_handle:
        pipeline_args = merge_dicts(
            {
                "pipeline_name": "foo",
                "external_pipeline_origin": pipeline_handle.get_external_origin(),
            },
            kwargs,
        )
        yield create_run_for_test(instance, **pipeline_args)


def test_submit_run(instance, coordinator):  # pylint: disable=redefined-outer-name
    with create_run(instance, run_id="foo-1", status=PipelineRunStatus.NOT_STARTED) as run:
        returned_run = call_submit_run(coordinator, run)
        assert returned_run.run_id == "foo-1"

        assert len(instance.run_launcher.queue()) == 0
        stored_run = instance.get_run_by_id("foo-1")
        assert stored_run.status == PipelineRunStatus.QUEUED


def test_submit_run_checks_status(instance, coordinator):  # pylint: disable=redefined-outer-name
    with create_run(instance, run_id="foo-1", status=PipelineRunStatus.QUEUED) as run:
        with pytest.raises(CheckError):
            call_submit_run(coordinator, run)
