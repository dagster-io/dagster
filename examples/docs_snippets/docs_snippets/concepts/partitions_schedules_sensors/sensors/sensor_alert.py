from dagster import ModeDefinition, ResourceDefinition, pipeline, sensor, solid
from dagster.core.definitions.run_request import RunRequest
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter
from dagster_slack import slack_resource


# start_alert_pipeline_marker
@solid(required_resource_keys={"slack"})
def slack_message_on_failure_solid(context):
    message = f"Solid {context.solid.name} failed"
    context.resources.slack.chat.post_message(channel="#foo", text=message)


@pipeline(
    mode_defs=[
        ModeDefinition(name="test", resource_defs={"slack": ResourceDefinition.mock_resource()}),
        ModeDefinition(name="prod", resource_defs={"slack": slack_resource}),
    ]
)
def failure_alert_pipeline():
    slack_message_on_failure_solid()


# end_alert_pipeline_marker


# start_alert_sensor_marker


@sensor(pipeline_name="failure_alert_pipeline", mode="prod")
def pipeline_failure_sensor(context):
    runs = context.instance.get_runs(
        filters=PipelineRunsFilter(
            pipeline_name="your_pipeline_name",
            statuses=[PipelineRunStatus.FAILURE],
        ),
    )
    for run in runs:
        # Use the id of the failed run as run_key to avoid duplicate alerts.
        yield RunRequest(run_key=str(run.run_id))


# end_alert_sensor_marker
