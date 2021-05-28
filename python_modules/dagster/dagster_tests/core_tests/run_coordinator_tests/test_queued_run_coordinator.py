import pytest
from dagster.check import CheckError
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.run_coordinator.queued_run_coordinator import QueuedRunCoordinator
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_run_for_test, environ, instance_for_test
from dagster.utils import merge_dicts
from dagster_tests.api_tests.utils import get_foo_external_pipeline


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
    run_coordinator.register_instance(instance)
    yield run_coordinator


def create_run(instance, external_pipeline, **kwargs):  # pylint: disable=redefined-outer-name
    pipeline_args = merge_dicts(
        {
            "pipeline_name": "foo",
            "external_pipeline_origin": external_pipeline.get_external_origin(),
        },
        kwargs,
    )
    return create_run_for_test(instance, **pipeline_args)


def test_config():
    with environ({"MAX_RUNS": "10", "DEQUEUE_INTERVAL": "7"}):
        with instance_for_test(
            overrides={
                "run_coordinator": {
                    "module": "dagster.core.run_coordinator",
                    "class": "QueuedRunCoordinator",
                    "config": {
                        "max_concurrent_runs": {
                            "env": "MAX_RUNS",
                        },
                        "tag_concurrency_limits": [
                            {"key": "foo", "value": "bar", "limit": 3},
                            {"key": "backfill", "limit": 2},
                        ],
                        "dequeue_interval_seconds": {
                            "env": "DEQUEUE_INTERVAL",
                        },
                    },
                }
            }
        ) as _:
            pass

    with pytest.raises(DagsterInvalidConfigError):
        with instance_for_test(
            overrides={
                "run_coordinator": {
                    "module": "dagster.core.run_coordinator",
                    "class": "QueuedRunCoordinator",
                    "config": {
                        "tag_concurrency_limits": [
                            {"key": "backfill"},
                        ],
                    },
                }
            }
        ) as _:
            pass


def test_submit_run(instance, coordinator):  # pylint: disable=redefined-outer-name
    with get_foo_external_pipeline() as external_pipeline:
        run = create_run(
            instance, external_pipeline, run_id="foo-1", status=PipelineRunStatus.NOT_STARTED
        )
        returned_run = coordinator.submit_run(run, external_pipeline)
        assert returned_run.run_id == "foo-1"
        assert returned_run.status == PipelineRunStatus.QUEUED

        assert len(instance.run_launcher.queue()) == 0
        stored_run = instance.get_run_by_id("foo-1")
        assert stored_run.status == PipelineRunStatus.QUEUED


def test_submit_run_checks_status(instance, coordinator):  # pylint: disable=redefined-outer-name
    with get_foo_external_pipeline() as external_pipeline:
        run = create_run(
            instance, external_pipeline, run_id="foo-1", status=PipelineRunStatus.QUEUED
        )
        with pytest.raises(CheckError):
            coordinator.submit_run(run, external_pipeline)


def test_cancel_run(instance, coordinator):  # pylint: disable=redefined-outer-name
    with get_foo_external_pipeline() as external_pipeline:
        run = create_run(
            instance, external_pipeline, run_id="foo-1", status=PipelineRunStatus.NOT_STARTED
        )
        assert not coordinator.can_cancel_run(run.run_id)

        coordinator.submit_run(run, external_pipeline)
        assert coordinator.can_cancel_run(run.run_id)

        coordinator.cancel_run(run.run_id)
        stored_run = instance.get_run_by_id("foo-1")
        assert stored_run.status == PipelineRunStatus.CANCELED
        assert not coordinator.can_cancel_run(run.run_id)
