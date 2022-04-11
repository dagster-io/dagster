from typing import Callable, Optional

from dagster_msteams.card import Card
from dagster_msteams.client import TeamsClient

from dagster import DefaultSensorStatus
from dagster.core.definitions.run_status_sensor_definition import (
    PipelineFailureSensorContext,
    pipeline_failure_sensor,
)


def _default_failure_message(context: PipelineFailureSensorContext) -> str:
    return "\n".join(
        [
            f"Pipeline {context.pipeline_run.pipeline_name} failed!",
            f"Run ID: {context.pipeline_run.run_id}",
            f"Mode: {context.pipeline_run.mode}",
            f"Error: {context.failure_event.message}",
        ]
    )


def make_teams_on_pipeline_failure_sensor(
    hook_url: str,
    message_fn: Callable[[PipelineFailureSensorContext], str] = _default_failure_message,
    http_proxy: Optional[str] = None,
    https_proxy: Optional[str] = None,
    timeout: Optional[float] = 60,
    verify: Optional[bool] = None,
    name: Optional[str] = None,
    dagit_base_url: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
):
    """Create a sensor on pipeline failures that will message the given MS Teams webhook URL.

    Args:
        hook_url (str): MS Teams incoming webhook URL.
        message_fn (Optional(Callable[[PipelineFailureSensorContext], str])): Function which
            takes in the ``PipelineFailureSensorContext`` and outputs the message you want to send.
            Defaults to a text message that contains error message, pipeline name, and run ID.
        http_proxy : (Optional[str]): Proxy for requests using http protocol.
        https_proxy : (Optional[str]): Proxy for requests using https protocol.
        timeout: (Optional[float]): Connection timeout in seconds. Defaults to 60.
        verify: (Optional[bool]): Whether to verify the servers TLS certificate.
        name: (Optional[str]): The name of the sensor. Defaults to "teams_on_pipeline_failure".
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the failed pipeline run.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.

    Examples:

        .. code-block:: python

            teams_on_pipeline_failure = make_teams_on_pipeline_failure_sensor(
                hook_url=os.getenv("TEAMS_WEBHOOK_URL")
            )

            @repository
            def my_repo():
                return [my_pipeline + teams_on_pipeline_failure]

        .. code-block:: python

            def my_message_fn(context: PipelineFailureSensorContext) -> str:
                return "Pipeline {pipeline_name} failed! Error: {error}".format(
                    pipeline_name=context.pipeline_run.pipeline_name,
                    error=context.failure_event.message,
                )

            teams_on_pipeline_failure = make_teams_on_pipeline_failure_sensor(
                hook_url=os.getenv("TEAMS_WEBHOOK_URL"),
                message_fn=my_message_fn,
                dagit_base_url="http://localhost:3000",
            )


    """

    teams_client = TeamsClient(
        hook_url=hook_url,
        http_proxy=http_proxy,
        https_proxy=https_proxy,
        timeout=timeout,
        verify=verify,
    )

    @pipeline_failure_sensor(name=name, default_status=default_status)
    def teams_on_pipeline_failure(context: PipelineFailureSensorContext):

        text = message_fn(context)
        if dagit_base_url:
            text += "<a href='{base_url}/instance/runs/{run_id}'>View in Dagit</a>".format(
                base_url=dagit_base_url,
                run_id=context.pipeline_run.run_id,
            )
        card = Card()
        card.add_attachment(text_message=text)
        teams_client.post_message(payload=card.payload)

    return teams_on_pipeline_failure
