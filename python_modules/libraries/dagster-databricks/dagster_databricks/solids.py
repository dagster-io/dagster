from dagster import (
    Field,
    InputDefinition,
    Int,
    Nothing,
    Output,
    OutputDefinition,
    SolidDefinition,
    String,
    check,
)

from .configs import define_databricks_submit_custom_run_config
from .databricks import DatabricksJobRunner

_START = "start"

# wait at most 24 hours by default for run execution
_DEFAULT_RUN_MAX_WAIT_TIME_SEC = 24 * 60 * 60


class DatabricksRunJobSolidDefinition(SolidDefinition):
    """Solid to run a Databricks job.

    The job configuration is passed entirely by config, and no code is synchronised to Databricks.
    See :py:class:`dagster_databricks.databricks_pyspark_step_launcher` to run PySpark solids within
    a Databricks job.
    """

    def __init__(
        self,
        name,
        description=None,
        poll_interval_sec=10,
        max_wait_time_sec=_DEFAULT_RUN_MAX_WAIT_TIME_SEC,
    ):
        name = check.str_param(name, "name")

        description = check.opt_str_param(
            description, "description", "Databricks run job flow solid."
        )

        def _compute_fn(context, _):

            job_runner = DatabricksJobRunner(
                host=context.solid_config.get("databricks_host"),
                token=context.solid_config.get("databricks_host"),
                poll_interval_sec=poll_interval_sec,
                max_wait_time_sec=max_wait_time_sec,
            )
            run_config = context.solid_config["run_config"].copy()
            task = run_config.pop("task")
            databricks_run_id = job_runner.submit_run(run_config, task)
            context.log.info("waiting for Databricks job completion...")

            job_runner.wait_for_run_to_complete(context.log, databricks_run_id)
            yield Output(databricks_run_id)

        super(DatabricksRunJobSolidDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=[InputDefinition(_START, Nothing)],
            output_defs=[OutputDefinition(Int)],
            compute_fn=_compute_fn,
            config_schema={
                "run_config": define_databricks_submit_custom_run_config(),
                "databricks_host": Field(String, is_required=False),
                "databricks_token": Field(String, is_required=True),
            },
        )
