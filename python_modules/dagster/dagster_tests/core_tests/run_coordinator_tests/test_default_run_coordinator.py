import pytest
from dagster_tests.api_tests.utils import get_bar_workspace

from dagster._check import CheckError
from dagster._utils import merge_dicts
from dagster._core.run_coordinator import SubmitRunContext
from dagster._core.run_coordinator.default_run_coordinator import DefaultRunCoordinator
from dagster._core.storage.pipeline_run import PipelineRunStatus
from dagster._core.test_utils import create_run_for_test, instance_for_test


@pytest.fixture()
def instance():
    overrides = {
        "run_launcher": {"module": "dagster.core.test_utils", "class": "MockedRunLauncher"}
    }
    with instance_for_test(overrides=overrides) as inst:
        yield inst


@pytest.fixture()
def coodinator(instance):  # pylint: disable=redefined-outer-name
    run_coordinator = DefaultRunCoordinator()
    run_coordinator.register_instance(instance)
    yield run_coordinator


def create_run(instance, external_pipeline, **kwargs):  # pylint: disable=redefined-outer-name
    pipeline_args = merge_dicts(
        {
            "pipeline_name": "foo",
            "external_pipeline_origin": external_pipeline.get_external_origin(),
            "pipeline_code_origin": external_pipeline.get_python_origin(),
        },
        kwargs,
    )
    return create_run_for_test(instance, **pipeline_args)


def test_submit_run(instance, coodinator):  # pylint: disable=redefined-outer-name
    with get_bar_workspace(instance) as workspace:
        external_pipeline = (
            workspace.get_repository_location("bar_repo_location")
            .get_repository("bar_repo")
            .get_full_external_pipeline("foo")
        )

        run = create_run(instance, external_pipeline, run_id="foo-1")
        returned_run = coodinator.submit_run(SubmitRunContext(run, workspace))
        assert returned_run.run_id == "foo-1"
        assert returned_run.status == PipelineRunStatus.STARTING

        assert len(instance.run_launcher.queue()) == 1
        assert instance.run_launcher.queue()[0].run_id == "foo-1"
        assert instance.run_launcher.queue()[0].status == PipelineRunStatus.STARTING
        assert instance.get_run_by_id("foo-1")


def test_submit_run_checks_status(instance, coodinator):  # pylint: disable=redefined-outer-name
    with get_bar_workspace(instance) as workspace:
        external_pipeline = (
            workspace.get_repository_location("bar_repo_location")
            .get_repository("bar_repo")
            .get_full_external_pipeline("foo")
        )

        run = create_run(
            instance, external_pipeline, run_id="foo-1", status=PipelineRunStatus.STARTED
        )
        with pytest.raises(CheckError):
            coodinator.submit_run(SubmitRunContext(run, workspace))
