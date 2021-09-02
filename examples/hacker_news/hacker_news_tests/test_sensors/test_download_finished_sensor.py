import tempfile
import uuid

from dagster import build_sensor_context, validate_run_config
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from hacker_news.jobs.dbt_metrics import dbt_prod_job
from hacker_news.jobs.hacker_news_api_download import DEFAULT_PARTITION_RESOURCE_CONFIG
from hacker_news.sensors.download_finished_sensor import dbt_on_hn_download_finished_prod


def test_no_runs():
    run_requests = list(
        dbt_on_hn_download_finished_prod(
            build_sensor_context(instance=DagsterInstance.local_temp())
        )
    )
    assert len(run_requests) == 0


def test_no_runs_for_different_pipeline():
    with tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        instance.add_run(PipelineRun(status=PipelineRunStatus.SUCCESS, pipeline_name="xyz"))
        run_requests = list(
            dbt_on_hn_download_finished_prod(build_sensor_context(instance=instance))
        )
        assert len(run_requests) == 0


def test_no_runs_for_failed_run():
    with tempfile.TemporaryDirectory() as temp_dir:

        instance = DagsterInstance.local_temp(temp_dir)
        instance.add_run(
            PipelineRun(
                status=PipelineRunStatus.FAILURE,
                pipeline_name="download_graph",
                run_config={"resources": DEFAULT_PARTITION_RESOURCE_CONFIG},
            )
        )
        run_requests = list(
            dbt_on_hn_download_finished_prod(build_sensor_context(instance=instance))
        )
        assert len(run_requests) == 0


def test_no_runs_for_invalid_config():
    with tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        instance.add_run(
            PipelineRun(
                status=PipelineRunStatus.FAILURE,
                pipeline_name="download_graph",
                run_config={"I'm some config": {"that is not": "valid"}},
            )
        )
        run_requests = list(
            dbt_on_hn_download_finished_prod(build_sensor_context(instance=instance))
        )
        assert len(run_requests) == 0


def test_multiple_runs_for_successful_runs():
    def get_should_launch_run():
        return PipelineRun(
            run_id=str(uuid.uuid4()),
            status=PipelineRunStatus.SUCCESS,
            pipeline_name="download_graph",
            run_config={"resources": DEFAULT_PARTITION_RESOURCE_CONFIG},
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        for run in [
            get_should_launch_run(),
            PipelineRun(status=PipelineRunStatus.FAILURE, pipeline_name="download_graph"),
            PipelineRun(status=PipelineRunStatus.SUCCESS, pipeline_name="weird_pipeline"),
            PipelineRun(status=PipelineRunStatus.SUCCESS, pipeline_name="other"),
            get_should_launch_run(),
            get_should_launch_run(),
            get_should_launch_run(),
        ]:
            instance.add_run(run)
        run_requests = list(
            dbt_on_hn_download_finished_prod(build_sensor_context(instance=instance))
        )
        assert len(run_requests) == 4
        for run_request in run_requests:
            assert validate_run_config(dbt_prod_job, run_request.run_config)
