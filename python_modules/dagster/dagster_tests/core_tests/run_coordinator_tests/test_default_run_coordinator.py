import pytest
from dagster._core.run_coordinator import SubmitRunContext
from dagster._core.run_coordinator.default_run_coordinator import DefaultRunCoordinator
from dagster._core.storage.pipeline_run import DagsterRunStatus
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._utils.merger import merge_dicts

from dagster_tests.api_tests.utils import get_bar_workspace


@pytest.fixture()
def instance():
    overrides = {
        "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"}
    }
    with instance_for_test(overrides=overrides) as inst:
        yield inst


@pytest.fixture()
def coodinator(instance):
    run_coordinator = DefaultRunCoordinator()
    run_coordinator.register_instance(instance)
    yield run_coordinator


def create_run(instance, external_pipeline, **kwargs):
    job_args = merge_dicts(
        {
            "pipeline_name": "foo",
            "external_pipeline_origin": external_pipeline.get_external_origin(),
            "pipeline_code_origin": external_pipeline.get_python_origin(),
        },
        kwargs,
    )
    return create_run_for_test(instance, **job_args)


def test_submit_run(instance, coodinator):
    with get_bar_workspace(instance) as workspace:
        external_job = (
            workspace.get_code_location("bar_code_location")
            .get_repository("bar_repo")
            .get_full_external_job("foo")
        )

        run = create_run(instance, external_job, run_id="foo-1")
        returned_run = coodinator.submit_run(SubmitRunContext(run, workspace))
        assert returned_run.run_id == "foo-1"
        assert returned_run.status == DagsterRunStatus.STARTING

        assert len(instance.run_launcher.queue()) == 1
        assert instance.run_launcher.queue()[0].run_id == "foo-1"
        assert instance.run_launcher.queue()[0].status == DagsterRunStatus.STARTING
        assert instance.get_run_by_id("foo-1")


def test_submit_run_checks_status(instance, coodinator):
    with get_bar_workspace(instance) as workspace:
        external_job = (
            workspace.get_code_location("bar_code_location")
            .get_repository("bar_repo")
            .get_full_external_job("foo")
        )

        run = create_run(instance, external_job, run_id="foo-1", status=DagsterRunStatus.STARTED)
        coodinator.submit_run(SubmitRunContext(run, workspace))

        # assert that runs not in a NOT_STARTED state are not launched
        assert len(instance.run_launcher.queue()) == 0
