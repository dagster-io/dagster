"""isort:skip_file"""


# start_alert_sensor_marker
import os
from dagster import pipeline_failure_sensor, PipelineFailureSensorContext
from slack_sdk import WebClient


@pipeline_failure_sensor
def my_slack_on_pipeline_failure(context: PipelineFailureSensorContext):
    slack_client = WebClient(token=os.environ["SLACK_DAGSTER_ETL_BOT_TOKEN"])

    slack_client.chat_postMessage(
        channel="#alert-channel",
        message=f'Pipeline "{context.pipeline_run.pipeline_name}" failed. Error: {context.failure_event.message}',
    )


# end_alert_sensor_marker


# start_slack_marker
from dagster_slack import make_slack_on_pipeline_failure_sensor

slack_on_pipeline_failure = make_slack_on_pipeline_failure_sensor(
    "#my_channel", os.getenv("MY_SLACK_TOKEN")
)


# end_slack_marker


# start_email_marker
from dagster.utils import make_email_on_pipeline_failure_sensor


email_on_pipeline_failure = make_email_on_pipeline_failure_sensor(
    email_from="no-reply@example.com",
    email_password=os.getenv("ALERT_EMAIL_PASSWORD"),
    email_to=["xxx@example.com", "xyz@example.com"],
)

# end_email_marker

# start_success_sensor_marker
from dagster import run_status_sensor, RunStatusSensorContext, PipelineRunStatus


@run_status_sensor(pipeline_run_status=PipelineRunStatus.SUCCESS)
def my_slack_on_pipeline_success(context: RunStatusSensorContext):
    slack_client = WebClient(token=os.environ["SLACK_DAGSTER_ETL_BOT_TOKEN"])

    slack_client.chat_postMessage(
        channel="#alert-channel",
        message=f'Pipeline "{context.pipeline_run.pipeline_name}" succeeded.',
    )


# end_success_sensor_marker

my_pipelines = []

# start_repo_marker
from dagster import repository


@repository
def my_repository():
    return my_pipelines + [my_slack_on_pipeline_success]


# end_repo_marker
