from typing import Optional

from dagster import (
    Field,
    In,
    Nothing,
    OpExecutionContext,
    Out,
    Output,
    Permissive,
    _check as check,
    op,
)
from dagster._core.definitions.op_definition import OpDefinition
from databricks_cli.sdk import JobsService

from .databricks import DatabricksClient

_DEFAULT_POLL_INTERVAL = 10
# wait at most 24 hours by default for run execution
_DEFAULT_RUN_MAX_WAIT_TIME_SEC = 24 * 60 * 60


def create_databricks_job_op(
    name="databricks_job",
    num_inputs=1,
    description=None,
    required_resource_keys=frozenset(["databricks_client"]),
):
    """
    Creates an op that launches a databricks job (not to be confused with Dagster's job API).

    As config, the op accepts a blob of the form described in Databricks' job API:
    https://docs.databricks.com/dev-tools/api/latest/jobs.html.

    Returns:
        OpDefinition: An op definition.

    Example:

        .. code-block:: python

            from dagster import job
            from dagster_databricks import create_databricks_job_op, databricks_client

            sparkpi = create_databricks_job_op().configured(
                {
                    "job": {
                        "run_name": "SparkPi Python job",
                        "new_cluster": {
                            "spark_version": "7.3.x-scala2.12",
                            "node_type_id": "i3.xlarge",
                            "num_workers": 2,
                        },
                        "spark_python_task": {"python_file": "dbfs:/docs/pi.py", "parameters": ["10"]},
                    }
                },
                name="sparkpi",
            )

            @job(
                resource_defs={
                    "databricks_client": databricks_client.configured(
                        {"host": "my.workspace.url", "token": "my.access.token"}
                    )
                }
            )
            def do_stuff():
                sparkpi()
    """
    check.str_param(name, "name")
    check.opt_str_param(description, "description")
    check.int_param(num_inputs, "num_inputs")
    check.set_param(required_resource_keys, "required_resource_keys", of_type=str)

    ins = {"input_" + str(i): In(Nothing) for i in range(num_inputs)}

    @op(
        name=name,
        description=description,
        config_schema={
            "job": Field(
                Permissive(),
                description=(
                    "Databricks job run configuration, in the form described in Databricks' job"
                    " API: https://docs.databricks.com/dev-tools/api/latest/jobs.html"
                ),
            ),
            "poll_interval_sec": Field(
                float,
                description="Check whether the job is done at this interval.",
                default_value=_DEFAULT_POLL_INTERVAL,
            ),
            "max_wait_time_sec": Field(
                float,
                description="If the job is not complete after this length of time, raise an error.",
                default_value=_DEFAULT_RUN_MAX_WAIT_TIME_SEC,
            ),
        },
        ins=ins,
        out=Out(Nothing),
        required_resource_keys=required_resource_keys,
        tags={"kind": "databricks"},
    )
    def databricks_fn(context):
        job_config = context.op_config["job"]
        databricks_client: DatabricksClient = context.resources.databricks_client

        run_id = JobsService(databricks_client.api_client).submit_run(**job_config)["run_id"]

        context.log.info(
            "Launched databricks job with run id {run_id}. UI: {url}. Waiting to run to"
            " completion...".format(
                run_id=run_id, url=create_ui_url(databricks_client, context.op_config)
            )
        )

        databricks_client.wait_for_run_to_complete(
            logger=context.log,
            databricks_run_id=run_id,
            poll_interval_sec=context.op_config["poll_interval_sec"],
            max_wait_time_sec=context.op_config["max_wait_time_sec"],
        )

    return databricks_fn


def create_ui_url(databricks_client, op_config):
    host = databricks_client.host
    workspace_id = databricks_client.workspace_id or "<workspace_id>"
    if "existing_cluster_id" in op_config["job"]:
        return "https://{host}/?o={workspace_id}#/setting/clusters/{cluster_id}/sparkUi".format(
            host=host,
            workspace_id=workspace_id,
            cluster_id=op_config["job"]["existing_cluster_id"],
        )
    else:
        return "https://{host}/?o={workspace_id}#joblist".format(
            host=host, workspace_id=workspace_id
        )


def create_databricks_run_now_op(
    databricks_job_id: int, databricks_job_configuration: Optional[dict] = None, **kwargs
) -> OpDefinition:
    """
    Creates an op that launches an existing databricks job.

    As config, the op accepts a blob of the form described in Databricks' Job API:
    https://docs.databricks.com/api-explorer/workspace/jobs/runnow. The only required field is
    ``job_id``, which is the ID of the job to be executed. Additional fields can be used to specify
    override parameters for the Databricks Job.

    Arguments:
        databricks_job_id (int): The ID of the Databricks Job to be executed.
        databricks_job_configuration (dict): Configuration for triggering a new job run of a
            Databricks Job. See https://docs.databricks.com/api-explorer/workspace/jobs/runnow
            for the full configuration.
        **kwargs: Additional keyword arguments to pass to the underlying op. Accepted keywords are
            are the accepted keywords to the @op decorator.

    Returns:
        OpDefinition: An op definition to run the Databricks Job.

    Example:
        .. code-block:: python

            from dagster import job
            from dagster_databricks import create_databricks_run_now_op, databricks_client

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
                    "databricks": databricks_client.configured(
                        {
                            "host": {"env": "DATABRICKS_HOST"},
                            "token": {"env": "DATABRICKS_TOKEN"}
                        }
                    )
                }
            )
            def do_stuff():
                run_now_op()
    """
    op_kwargs = {
        "ins": {"start_after": In(Nothing)},
        "config_schema": {
            "job": Field(
                config=Permissive(),
                is_required=False,
                description=(
                    "Configuration for triggering a run of an existing Databricks Job. See"
                    " https://docs.databricks.com/api-explorer/workspace/jobs/runnow for the"
                    " full configuration."
                ),
            ),
            "poll_interval_sec": Field(
                float,
                description="Check whether the Databricks Job is done at this interval.",
                default_value=_DEFAULT_POLL_INTERVAL,
            ),
            "max_wait_time_sec": Field(
                float,
                description=(
                    "If the Databricks Job is not complete after this length of time, raise an"
                    " error."
                ),
                default_value=_DEFAULT_RUN_MAX_WAIT_TIME_SEC,
            ),
        },
        "required_resource_keys": {"databricks"},
        "tags": {"kind": "databricks"},
        **kwargs,
    }

    @op(**op_kwargs)
    def _databricks_run_now_op(context: OpExecutionContext):
        databricks: DatabricksClient = context.resources.databricks
        jobs_service = JobsService(databricks.api_client)

        run_id: int = jobs_service.run_now(
            job_id=databricks_job_id,
            **{
                **(databricks_job_configuration or {}),
                **context.op_config.get("job", {}),
            },
        )["run_id"]

        get_run_response: dict = jobs_service.get_run(run_id=run_id)

        context.log.info(
            f"Launched databricks job run for '{get_run_response['run_name']}' (`{run_id}`). URL:"
            f" {get_run_response['run_page_url']}. Waiting to run to complete."
        )

        databricks.wait_for_run_to_complete(
            logger=context.log,
            databricks_run_id=run_id,
            poll_interval_sec=context.op_config["poll_interval_sec"],
            max_wait_time_sec=context.op_config["max_wait_time_sec"],
        )

        yield from [
            Output(value=None, output_name=output_name)
            for output_name in context.op.output_dict.keys()
        ]

    return _databricks_run_now_op


def create_databricks_submit_run_op(
    databricks_job_configuration: dict,
    **kwargs,
) -> OpDefinition:
    """
    Creates an op that submits a one-time run of a set of tasks on Databricks.

    As config, the op accepts a blob of the form described in Databricks' Job API:
    https://docs.databricks.com/api-explorer/workspace/jobs/submit.

    Arguments:
        databricks_job_configuration (dict): Configuration for submitting a one-time run of a set
            of tasks on Databricks. See https://docs.databricks.com/api-explorer/workspace/jobs/submit
            for the full configuration.
        **kwargs: Additional keyword arguments to pass to the underlying op. Accepted keywords are
            are the accepted keywords to the @op decorator.

    Returns:
        OpDefinition: An op definition to submit a one-time run of a set of tasks on Databricks.

    Example:
        .. code-block:: python

            from dagster import job
            from dagster_databricks import create_databricks_submit_run_op, databricks_client

            DATABRICKS_JOB_ID = 1234

            submit_run_op = create_databricks_submit_run_op(
                databricks_job_configuration={
                    "job": {
                        "new_cluster": {
                            "spark_version": '2.1.0-db3-scala2.11',
                            "num_workers": 2
                        },
                        "notebook_task": {
                            "notebook_path": "/Users/dagster@example.com/PrepareData",
                        },
                    }
                }
            )

            @job(
                resource_defs={
                    "databricks": databricks_client.configured(
                        {
                            "host": {"env": "DATABRICKS_HOST"},
                            "token": {"env": "DATABRICKS_TOKEN"}
                        }
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

    op_kwargs = {
        "ins": {"start_after": In(Nothing)},
        "config_schema": {
            "job": Field(
                config=Permissive(),
                is_required=False,
                description=(
                    "Configuration for submitting a one-time run of a set of tasks on Databricks."
                    " See https://docs.databricks.com/api-explorer/workspace/jobs/submit for the"
                    " full configuration."
                ),
            ),
            "poll_interval_sec": Field(
                float,
                description="Check whether the Databricks Job is done at this interval.",
                default_value=_DEFAULT_POLL_INTERVAL,
            ),
            "max_wait_time_sec": Field(
                float,
                description=(
                    "If the Databricks Job is not complete after this length of time, raise an"
                    " error."
                ),
                default_value=_DEFAULT_RUN_MAX_WAIT_TIME_SEC,
            ),
        },
        "required_resource_keys": {"databricks"},
        "tags": {"kind": "databricks"},
        **kwargs,
    }

    @op(**op_kwargs)
    def _databricks_submit_run_op(context: OpExecutionContext):
        databricks: DatabricksClient = context.resources.databricks
        jobs_service = JobsService(databricks.api_client)

        run_id: int = jobs_service.submit_run(
            **databricks_job_configuration,
            **context.op_config.get("job", {}),
        )["run_id"]

        get_run_response: dict = jobs_service.get_run(run_id=run_id)

        context.log.info(
            f"Launched databricks job run for '{get_run_response['run_name']}' (`{run_id}`). URL:"
            f" {get_run_response['run_page_url']}. Waiting to run to complete."
        )

        databricks.wait_for_run_to_complete(
            logger=context.log,
            databricks_run_id=run_id,
            poll_interval_sec=context.op_config["poll_interval_sec"],
            max_wait_time_sec=context.op_config["max_wait_time_sec"],
        )

        yield from [
            Output(value=None, output_name=output_name)
            for output_name in context.op.output_dict.keys()
        ]

    return _databricks_submit_run_op
