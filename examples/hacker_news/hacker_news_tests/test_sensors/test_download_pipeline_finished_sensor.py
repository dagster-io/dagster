import tempfile
import uuid

from dagster import build_sensor_context, validate_run_config
from dagster.core.instance import DagsterInstance
from dagster.core.storage.dagster_run import DagsterRun, DagsterRunStatus, PipelineTarget
from hacker_news.pipelines.dbt_pipeline import dbt_pipeline
from hacker_news.pipelines.download_pipeline import DEFAULT_PARTITION_RESOURCE_CONFIG
from hacker_news.sensors.download_pipeline_finished_sensor import dbt_on_hn_download_finished


def test_no_runs():
    run_requests = list(
        dbt_on_hn_download_finished(build_sensor_context(instance=DagsterInstance.local_temp()))
    )
    assert len(run_requests) == 0


def test_no_runs_for_different_pipeline():
    with tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        target = PipelineTarget(name="xyz", mode="prod")
        instance.add_run(DagsterRun(status=DagsterRunStatus.SUCCESS, target=target))
        run_requests = list(dbt_on_hn_download_finished(build_sensor_context(instance=instance)))
        assert len(run_requests) == 0


def test_no_runs_for_different_mode():
    with tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        target = PipelineTarget(name="download_pipeline", mode="prod")
        instance.add_run(DagsterRun(status=DagsterRunStatus.SUCCESS, target=target))
        run_requests = list(dbt_on_hn_download_finished(build_sensor_context(instance=instance)))
        assert len(run_requests) == 0


def test_no_runs_for_failed_run():
    with tempfile.TemporaryDirectory() as temp_dir:

        instance = DagsterInstance.local_temp(temp_dir)
        target = PipelineTarget(name="download_pipeline", mode="prod")
        instance.add_run(
            DagsterRun(
                status=DagsterRunStatus.FAILURE,
                target=target,
                run_config={"resources": DEFAULT_PARTITION_RESOURCE_CONFIG},
            )
        )
        run_requests = list(dbt_on_hn_download_finished(build_sensor_context(instance=instance)))
        assert len(run_requests) == 0


def test_no_runs_for_invalid_config():
    with tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        target = PipelineTarget(name="download_pipeline", mode="prod")
        instance.add_run(
            DagsterRun(
                status=DagsterRunStatus.FAILURE,
                target=target,
                run_config={"I'm some config": {"that is not": "valid"}},
            )
        )
        run_requests = list(dbt_on_hn_download_finished(build_sensor_context(instance=instance)))
        assert len(run_requests) == 0


def test_multiple_runs_for_successful_runs():
    def get_should_launch_run():
        target = PipelineTarget(name="download_pipeline", mode="prod")
        return DagsterRun(
            run_id=str(uuid.uuid4()),
            status=DagsterRunStatus.SUCCESS,
            target=target,
            run_config={"resources": DEFAULT_PARTITION_RESOURCE_CONFIG},
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        for run in [
            get_should_launch_run(),
            DagsterRun(
                status=DagsterRunStatus.FAILURE,
                target=PipelineTarget(mode="prod", name="download_pipeline"),
            ),
            DagsterRun(
                status=DagsterRunStatus.SUCCESS,
                target=PipelineTarget(mode="dev", name="weird_pipeline"),
            ),
            DagsterRun(
                status=DagsterRunStatus.SUCCESS,
                target=PipelineTarget(mode="test", name="download_pipeline"),
            ),
            DagsterRun(
                status=DagsterRunStatus.SUCCESS,
                target=PipelineTarget(mode="prod", name="other"),
            ),
            get_should_launch_run(),
            get_should_launch_run(),
            get_should_launch_run(),
        ]:
            instance.add_run(run)
        run_requests = list(dbt_on_hn_download_finished(build_sensor_context(instance=instance)))
        assert len(run_requests) == 4
        for run_request in run_requests:
            assert validate_run_config(dbt_pipeline, run_request.run_config)
