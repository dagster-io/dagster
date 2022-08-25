from dagster import Field, In, Nothing, Out, Permissive
from dagster import _check as check
from dagster import op

from .databricks import wait_for_run_to_complete

_START = "start"

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

            from dagster import graph
            from dagster_databricks import create_databricks_job_op, databricks_client

            sparkpi = create_databricks_job_op().configured(
                {
                    "job": {
                        "name": "SparkPi Python job",
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

            @graph
            def my_spark():
                sparkpi()

            my_spark.to_job(
                resource_defs={
                    "databricks_client": databricks_client.configured(
                        {"host": "my.workspace.url", "token": "my.access.token"}
                    )
                }
            )
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
                description="Databricks job run configuration, in the form described in "
                "Databricks' job API: https://docs.databricks.com/dev-tools/api/latest/jobs.html",
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
        databricks_client = context.resources.databricks_client
        run_id = databricks_client.submit_run(**job_config)

        context.log.info(
            "Launched databricks job with run id {run_id}. UI: {url}. Waiting to run to completion...".format(
                run_id=run_id, url=create_ui_url(databricks_client, context.op_config)
            )
        )
        wait_for_run_to_complete(
            databricks_client,
            context.log,
            run_id,
            context.op_config["poll_interval_sec"],
            context.op_config["max_wait_time_sec"],
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
