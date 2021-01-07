from dagster import Field, InputDefinition, Nothing, OutputDefinition, Permissive, check, solid

from .databricks import wait_for_run_to_complete

_START = "start"

_DEFAULT_POLL_INTERVAL = 10
# wait at most 24 hours by default for run execution
_DEFAULT_RUN_MAX_WAIT_TIME_SEC = 24 * 60 * 60


def create_databricks_job_solid(
    name="databricks_job",
    num_inputs=1,
    description=None,
    required_resource_keys=frozenset(["databricks_client"]),
):
    """
    Creates a solid that launches a databricks job.

    As config, the solid accepts a blob of the form described in Databricks' job API:
    https://docs.databricks.com/dev-tools/api/latest/jobs.html.

    Returns:
        SolidDefinition: A solid definition.
    """
    check.str_param(name, "name")
    check.opt_str_param(description, "description")
    check.int_param(num_inputs, "num_inputs")
    check.set_param(required_resource_keys, "required_resource_keys", of_type=str)

    input_defs = [InputDefinition("input_" + str(i), Nothing) for i in range(num_inputs)]

    @solid(
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
        input_defs=input_defs,
        output_defs=[OutputDefinition(Nothing)],
        required_resource_keys=required_resource_keys,
        tags={"kind": "databricks"},
    )
    def databricks_solid(context):
        job_config = context.solid_config["job"]
        databricks_client = context.resources.databricks_client
        run_id = databricks_client.submit_run(**job_config)

        context.log.info(
            "Launched databricks job with run id {run_id}. UI: {url}. Waiting to run to completion...".format(
                run_id=run_id, url=create_ui_url(databricks_client, context.solid_config)
            )
        )
        wait_for_run_to_complete(
            databricks_client,
            context.log,
            run_id,
            context.solid_config["poll_interval_sec"],
            context.solid_config["max_wait_time_sec"],
        )

    return databricks_solid


def create_ui_url(databricks_client, solid_config):
    host = databricks_client.host
    workspace_id = databricks_client.workspace_id or "<workspace_id>"
    if "existing_cluster_id" in solid_config["job"]:
        return "https://{host}/?o={workspace_id}#/setting/clusters/{cluster_id}/sparkUi".format(
            host=host,
            workspace_id=workspace_id,
            cluster_id=solid_config["job"]["existing_cluster_id"],
        )
    else:
        return "https://{host}/?o={workspace_id}#joblist".format(
            host=host, workspace_id=workspace_id
        )
