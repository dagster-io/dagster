from typing import Iterator

import pytest
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external import RemoteJob
from dagster._core.run_coordinator import SubmitRunContext
from dagster._core.run_coordinator.base import RunCoordinator
from dagster._core.run_coordinator.default_run_coordinator import DefaultRunCoordinator
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._utils.merger import merge_dicts

from dagster_tests.api_tests.utils import get_bar_workspace


@pytest.fixture()
def instance() -> Iterator[DagsterInstance]:
    overrides = {
        "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"}
    }
    with instance_for_test(overrides=overrides) as inst:
        yield inst


@pytest.fixture()
def coodinator(instance: DagsterInstance) -> Iterator[RunCoordinator]:
    run_coordinator = DefaultRunCoordinator()
    run_coordinator.register_instance(instance)
    yield run_coordinator


def _create_run(
    instance: DagsterInstance, external_pipeline: RemoteJob, **kwargs: object
) -> DagsterRun:
    job_args = merge_dicts(
        {
            "job_name": "foo",
            "remote_job_origin": external_pipeline.get_remote_origin(),
            "job_code_origin": external_pipeline.get_python_origin(),
        },
        kwargs,
    )
    return create_run_for_test(instance, **job_args)


def test_submit_run(instance: DagsterInstance, coodinator: DefaultRunCoordinator):
    with get_bar_workspace(instance) as workspace:
        remote_job = (
            workspace.get_code_location("bar_code_location")
            .get_repository("bar_repo")
            .get_full_job("foo")
        )

        run = _create_run(instance, remote_job)
        returned_run = coodinator.submit_run(SubmitRunContext(run, workspace))
        assert returned_run.run_id == run.run_id
        assert returned_run.status == DagsterRunStatus.STARTING

        assert len(instance.run_launcher.queue()) == 1  # type: ignore
        assert instance.run_launcher.queue()[0].run_id == run.run_id  # type: ignore
        assert instance.run_launcher.queue()[0].status == DagsterRunStatus.STARTING  # type: ignore
        assert instance.get_run_by_id(run.run_id)


def test_submit_run_checks_status(instance: DagsterInstance, coodinator: DefaultRunCoordinator):
    with get_bar_workspace(instance) as workspace:
        remote_job = (
            workspace.get_code_location("bar_code_location")
            .get_repository("bar_repo")
            .get_full_job("foo")
        )

        run = _create_run(instance, remote_job, status=DagsterRunStatus.STARTED)
        coodinator.submit_run(SubmitRunContext(run, workspace))

        # assert that runs not in a NOT_STARTED state are not launched
        assert len(instance.run_launcher.queue()) == 0  # type: ignore
