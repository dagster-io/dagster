from typing import TYPE_CHECKING, Optional

from dagster import (
    In,
    Nothing,
    OpExecutionContext,
    _check as check,
    op,
)
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from databricks.sdk.service import jobs
from pydantic import Field

DEFAULT_POLL_INTERVAL_SECONDS = 10
# wait at most 24 hours by default for run execution
DEFAULT_MAX_WAIT_TIME_SECONDS = 24 * 60 * 60
from dagster import Config

if TYPE_CHECKING:
    from dagster_databricks.databricks import DatabricksClient


def create_databricks_run_now_op(
    databricks_job_id: int,
    databricks_job_configuration: Optional[dict] = None,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_wait_time_seconds: float = DEFAULT_MAX_WAIT_TIME_SECONDS,
    name: Optional[str] = None,
    databricks_resource_key: str = "databricks",
) -> OpDefinition:
    """Creates an op that launches an existing databricks job.

    As config, the op accepts a blob of the form described in Databricks' Job API:
    https://docs.databricks.com/api/workspace/jobs/runnow. The only required field is
    ``job_id``, which is the ID of the job to be executed. Additional fields can be used to specify
    override parameters for the Databricks Job.

    Arguments:
        databricks_job_id (int): The ID of the Databricks Job to be executed.
        databricks_job_configuration (dict): Configuration for triggering a new job run of a
            Databricks Job. See https://docs.databricks.com/api/workspace/jobs/runnow
            for the full configuration.
        poll_interval_seconds (float): How often to poll the Databricks API to check whether the
            Databricks job has finished running.
        max_wait_time_seconds (float): How long to wait for the Databricks job to finish running
            before raising an error.
        name (Optional[str]): The name of the op. If not provided, the name will be
            _databricks_run_now_op.
        databricks_resource_key (str): The name of the resource key used by this op. If not
            provided, the resource key will be "databricks".

    Returns:
        OpDefinition: An op definition to run the Databricks Job.

    Example:
        .. code-block:: python

            from dagster import job
            from dagster_databricks import create_databricks_run_now_op, DatabricksClientResource

            DATABRICKS_JOB_ID = 1234


            run_now_op = create_databricks_run_now_op(
                databricks_job_id=DATABRICKS_JOB_ID,
                databricks_job_configuration={
                    "python_params": [
                        "--input",
                        "schema.db.input_table",
                        "--output",
                        "schema.db.output_table",
                    ],
                },
            )

            @job(
                resource_defs={
                    "databricks": DatabricksClientResource(
                        host=EnvVar("DATABRICKS_HOST"),
                        token=EnvVar("DATABRICKS_TOKEN")
                    )
                }
            )
            def do_stuff():
                run_now_op()
    """
    _poll_interval_seconds = poll_interval_seconds
    _max_wait_time_seconds = max_wait_time_seconds

    class DatabricksRunNowOpConfig(Config):
        poll_interval_seconds: float = Field(
            default=_poll_interval_seconds,
            description="Check whether the Databricks Job is done at this interval, in seconds.",
        )
        max_wait_time_seconds: float = Field(
            default=_max_wait_time_seconds,
            description=(
                "If the Databricks Job is not complete after this length of time, in seconds,"
                " raise an error."
            ),
        )

    @op(
        ins={"start_after": In(Nothing)},
        required_resource_keys={databricks_resource_key},
        tags={COMPUTE_KIND_TAG: "databricks"},
        name=name,
    )
    def _databricks_run_now_op(context: OpExecutionContext, config: DatabricksRunNowOpConfig):
        databricks: DatabricksClient = getattr(context.resources, databricks_resource_key)
        jobs_service = databricks.workspace_client.jobs

        run = jobs_service.run_now(
            job_id=databricks_job_id,
            **(databricks_job_configuration or {}),
        )
        run_id = run.bind()["run_id"]

        get_run_response = jobs_service.get_run(run_id=run_id)

        context.log.info(
            f"Launched databricks job run for '{get_run_response.run_name}' (`{run_id}`). URL:"
            f" {get_run_response.run_page_url}. Waiting to run to complete."
        )

        databricks.wait_for_run_to_complete(
            logger=context.log,
            databricks_run_id=run_id,
            poll_interval_sec=config.poll_interval_seconds,
            max_wait_time_sec=config.max_wait_time_seconds,
        )

    return _databricks_run_now_op


def create_databricks_submit_run_op(
    databricks_job_configuration: dict,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_wait_time_seconds: float = DEFAULT_MAX_WAIT_TIME_SECONDS,
    name: Optional[str] = None,
    databricks_resource_key: str = "databricks",
) -> OpDefinition:
    """Creates an op that submits a one-time run of a set of tasks on Databricks.

    As config, the op accepts a blob of the form described in Databricks' Job API:
    https://docs.databricks.com/api/workspace/jobs/submit.

    Arguments:
        databricks_job_configuration (dict): Configuration for submitting a one-time run of a set
            of tasks on Databricks. See https://docs.databricks.com/api/workspace/jobs/submit
            for the full configuration.
        poll_interval_seconds (float): How often to poll the Databricks API to check whether the
            Databricks job has finished running.
        max_wait_time_seconds (float): How long to wait for the Databricks job to finish running
            before raising an error.
        name (Optional[str]): The name of the op. If not provided, the name will be
            _databricks_submit_run_op.
        databricks_resource_key (str): The name of the resource key used by this op. If not
            provided, the resource key will be "databricks".

    Returns:
        OpDefinition: An op definition to submit a one-time run of a set of tasks on Databricks.

    Example:
        .. code-block:: python

            from dagster import job
            from dagster_databricks import create_databricks_submit_run_op, DatabricksClientResource


            submit_run_op = create_databricks_submit_run_op(
                databricks_job_configuration={
                    "new_cluster": {
                        "spark_version": '2.1.0-db3-scala2.11',
                        "num_workers": 2
                    },
                    "notebook_task": {
                        "notebook_path": "/Users/dagster@example.com/PrepareData",
                    },
                }
            )

            @job(
                resource_defs={
                    "databricks": DatabricksClientResource(
                        host=EnvVar("DATABRICKS_HOST"),
                        token=EnvVar("DATABRICKS_TOKEN")
                    )
                }
            )
            def do_stuff():
                submit_run_op()
    """
    check.invariant(
        bool(databricks_job_configuration),
        "Configuration for the one-time Databricks Job is required.",
    )

    _poll_interval_seconds = poll_interval_seconds
    _max_wait_time_seconds = max_wait_time_seconds

    class DatabricksSubmitRunOpConfig(Config):
        poll_interval_seconds: float = Field(
            default=_poll_interval_seconds,
            description="Check whether the Databricks Job is done at this interval, in seconds.",
        )
        max_wait_time_seconds: float = Field(
            default=_max_wait_time_seconds,
            description=(
                "If the Databricks Job is not complete after this length of time, in seconds,"
                " raise an error."
            ),
        )

    @op(
        ins={"start_after": In(Nothing)},
        required_resource_keys={databricks_resource_key},
        tags={COMPUTE_KIND_TAG: "databricks"},
        name=name,
    )
    def _databricks_submit_run_op(
        context: OpExecutionContext, config: DatabricksSubmitRunOpConfig
    ) -> None:
        databricks: DatabricksClient = getattr(context.resources, databricks_resource_key)
        jobs_service = databricks.workspace_client.jobs

        run = jobs_service.submit(
            tasks=[jobs.SubmitTask.from_dict(databricks_job_configuration)],
        )
        run_id: int = run.bind()["run_id"]

        get_run_response = jobs_service.get_run(run_id=run_id)

        context.log.info(
            f"Launched databricks job run for '{get_run_response.run_name}' (`{run_id}`). URL:"
            f" {get_run_response.run_page_url}. Waiting to run to complete."
        )

        databricks.wait_for_run_to_complete(
            logger=context.log,
            databricks_run_id=run_id,
            poll_interval_sec=config.poll_interval_seconds,
            max_wait_time_sec=config.max_wait_time_seconds,
        )

    return _databricks_submit_run_op
