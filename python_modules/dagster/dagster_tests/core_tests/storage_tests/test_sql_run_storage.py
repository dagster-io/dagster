from ...utils import create_run

from dagster import DagsterRunStatus, RunsFilter

def test_latest_failed_only_filter(instance):
    parent_run_id = "retry-root"

    run1 = create_run(
        instance,
        run_id="run1",
        status=DagsterRunStatus.FAILURE,
        tags={"dagster/parent_run_id": parent_run_id},
        start_time=1000,
    )

    run2 = create_run(
        instance,
        run_id="run2",
        status=DagsterRunStatus.FAILURE,
        tags={"dagster/parent_run_id": parent_run_id},
        start_time=2000,
    )

    run3 = create_run(
        instance,
        run_id="run3",
        status=DagsterRunStatus.FAILURE,
        tags={"dagster/parent_run_id": parent_run_id},
        start_time=3000,
    )

    result = instance.get_run_records(
        filters=RunsFilter(
            status=[DagsterRunStatus.FAILURE],
            latest_failed_only=True
        )
    )

    assert len(result) == 1
    assert result[0].dagster_run.run_id == "run3"
