import sys

from dagster import (
    DagsterEventType,
    DagsterRun,
    DagsterRunStatus,
)
from dagster._core.host_representation import (
    ExternalRepositoryOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin


def _create_test_run(job_name: str, status: DagsterRunStatus) -> DagsterRun:
    origin_one = ExternalRepositoryOrigin(
        ManagedGrpcPythonEnvCodeLocationOrigin(
            LoadableTargetOrigin(
                executable_path=sys.executable, module_name="fake", attribute="fake"
            ),
        ),
        "fake",
    ).get_job_origin("fake")

    return DagsterRun(
        job_name=job_name,
        run_config=None,
        status=status,
        external_job_origin=origin_one,
    )


def _assert_run_has_canceled_events(instance, run_id) -> None:
    logs = instance.all_logs(run_id)
    assert len(logs) == 2
    assert logs[0].dagster_event.event_type == DagsterEventType.RUN_CANCELING
    assert logs[1].dagster_event.event_type == DagsterEventType.RUN_CANCELED


def test_cancel_all_queued_runs():
    with instance_for_test() as instance:
        run_ids = []

        job_names = [
            ("job_one", DagsterRunStatus.QUEUED),
            ("job_two", DagsterRunStatus.QUEUED),
            ("job_three", DagsterRunStatus.NOT_STARTED),
        ]
        for job_name, status in job_names:
            run = instance.run_storage.add_run(_create_test_run(job_name, status))
            run_ids.append(run.run_id)

        runs = instance.run_storage.get_runs()
        assert len(runs) == 3

        instance.cancel_queued_runs()

        run1 = instance.get_run_by_id(run_ids[0])
        assert run1.status == DagsterRunStatus.CANCELED
        assert run1.job_name == "job_one"
        _assert_run_has_canceled_events(instance, run_ids[0])

        run2 = instance.get_run_by_id(run_ids[1])
        assert run2.status == DagsterRunStatus.CANCELED
        assert run2.job_name == "job_two"
        _assert_run_has_canceled_events(instance, run_ids[1])

        run3 = instance.get_run_by_id(run_ids[2])
        assert run3.status == DagsterRunStatus.NOT_STARTED
        assert run3.job_name == "job_three"
        assert len(instance.all_logs(run_ids[2])) == 0
