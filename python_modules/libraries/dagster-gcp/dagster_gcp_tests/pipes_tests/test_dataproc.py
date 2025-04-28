from unittest.mock import MagicMock

import dagster as dg
import pytest
from dagster._core.pipes import open_pipes_session
from dagster_gcp.pipes.clients.dataproc_job import (
    JOB_TYPES_WITH_ARGS,
    PipesDataprocJobClient,
    SubmitJobParams,
)
from google.cloud.dataproc_v1 import (
    FlinkJob,
    HadoopJob,
    PySparkJob,
    SparkJob,
    SparkRJob,
    SubmitJobRequest,
)


@pytest.mark.parametrize("job_type", JOB_TYPES_WITH_ARGS)
def test_dataproc_job_submit_call(job_type: str):
    @dg.asset
    def my_asset(context: dg.AssetExecutionContext, dataproc_job_client: PipesDataprocJobClient):
        cmd = ["echo", "hello"]

        params = SubmitJobParams({"request": SubmitJobRequest()})

        assert "request" in params

        if job_type == "hadoop_job":
            params["request"].job.hadoop_job = HadoopJob(
                main_jar_file_uri="gs://dagster-pipes/script.py", args=cmd
            )
        elif job_type == "spark_job":
            params["request"].job.spark_job = SparkJob(
                main_jar_file_uri="gs://dagster-pipes/script.py", args=cmd
            )
        elif job_type == "pyspark_job":
            params["request"].job.pyspark_job = PySparkJob(
                main_python_file_uri="gs://dagster-pipes/script.py", args=cmd
            )
        elif job_type == "spark_r_job":
            params["request"].job.spark_r_job = SparkRJob(
                main_r_file_uri="gs://dagster-pipes/script.py", args=cmd
            )
        elif job_type == "flink_job":
            params["request"].job.flink_job = FlinkJob(
                main_jar_file_uri="gs://dagster-pipes/script.py", args=cmd
            )
        else:
            raise ValueError(f"Test not implemented for job type: {job_type}")

        with open_pipes_session(
            context=context,
            message_reader=dataproc_job_client.message_reader,
            context_injector=dg.PipesEnvContextInjector(),
        ) as session:
            params = dataproc_job_client._enrich_submit_job_params(  # noqa: SLF001
                context=context, session=session, params=params
            )
            assert "request" in params

            assert params["request"].job.labels["dagster-run-id"] == str(context.run_id)

            assert "--dagster-pipes-context" in getattr(params["request"].job, job_type).args
            assert "--dagster-pipes-messages" in getattr(params["request"].job, job_type).args

            dataproc_job_client._start(context=context, params=params)  # noqa: SLF001

            yield from session.get_results()

    dataproc_client = MagicMock()

    with dg.instance_for_test() as instance:
        dg.materialize(
            [my_asset],
            instance=instance,
            resources={
                "dataproc_job_client": PipesDataprocJobClient(
                    client=dataproc_client,
                    message_reader=dg.PipesTempFileMessageReader(),  # this doesn't matter since we won't be actually running Pipes
                )
            },
            raise_on_error=True,
        )

        assert dataproc_client.submit_job.call_count == 1
