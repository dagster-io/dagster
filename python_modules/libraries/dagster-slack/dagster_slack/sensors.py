from typing import Callable, Optional

from dagster.core.definitions.pipeline_sensor import (
    PipelineFailureSensorContext,
    pipeline_failure_sensor,
)
from slack import WebClient


def _default_failure_message(context: PipelineFailureSensorContext) -> str:
    return "\n".join(
        [
            f"Pipeline {context.pipeline_run.pipeline_name} failed!",
            f"Run ID: {context.pipeline_run.run_id}",
            f"Mode: {context.pipeline_run.mode}",
            f"Error: {context.failure_event.message}",
        ]
    )


def make_slack_on_pipeline_failure_sensor(
    channel: str,
    slack_token: str,
    message_fn: Callable[[PipelineFailureSensorContext], str] = _default_failure_message,
    name: Optional[str] = None,
    dagit_base_url: Optional[str] = None,
):
    """Create a sensor on pipeline failures that will message the given Slack channel.

    Args:
        channel (str): The channel to send the message to (e.g. "#my_channel")
        slack_token (str): The slack token.
            Tokens are typically either user tokens or bot tokens. More in the Slack API
            documentation here: https://api.slack.com/docs/token-types
        message_fn (Optional(Callable[[PipelineFailureSensorContext], str])): Function which
            takes in the ``PipelineFailureSensorContext`` and outputs the message you want to send.
            Defaults to a text message that contains error message, pipeline name, and run ID.
        name: (Optional[str]): The name of the sensor. Defaults to "slack_on_pipeline_failure".
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the failed pipeline run.

    Examples:

        .. code-block:: python

            slack_on_pipeline_failure = make_slack_on_pipeline_failure_sensor(
                "#my_channel",
                os.getenv("MY_SLACK_TOKEN")
            )

            @repository
            def my_repo():
                return [my_pipeline + slack_on_pipeline_failure]

        .. code-block:: python

            def my_message_fn(context: PipelineFailureSensorContext) -> str:
                return "Pipeline {pipeline_name} failed! Error: {error}".format(
                    pipeline_name=context.pipeline_run.pipeline_name,
                    error=context.failure_event.message,
                )

            slack_on_pipeline_failure = make_slack_on_pipeline_failure_sensor(
                channel="#my_channel",
                slack_token=os.getenv("MY_SLACK_TOKEN"),
                message_fn=my_message_fn,
                dagit_base_url="http://mycoolsite.com",
            )


    """

    slack_client = WebClient(token=slack_token)

    @pipeline_failure_sensor(name=name)
    def slack_on_pipeline_failure(context: PipelineFailureSensorContext):

        text = message_fn(context)
        if dagit_base_url:
            text += "\n<{base_url}/instance/runs/{run_id}|View in Dagit>".format(
                base_url=dagit_base_url, run_id=context.pipeline_run.run_id
            )

        slack_client.chat_postMessage(channel=channel, text=text)

    return slack_on_pipeline_failure
