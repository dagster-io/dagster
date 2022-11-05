from typing import TYPE_CHECKING, Callable, List, Optional, Union

from dagster_msteams.card import Card
from dagster_msteams.client import TeamsClient

from dagster import DefaultSensorStatus
from dagster._core.definitions import GraphDefinition, PipelineDefinition
from dagster._core.definitions.run_status_sensor_definition import (
    RunFailureSensorContext,
    run_failure_sensor,
)
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

if TYPE_CHECKING:
    from dagster._core.host_representation.selector import JobSelector, RepositorySelector


def _default_failure_message(context: RunFailureSensorContext) -> str:
    return "\n".join(
        [
            f"Job {context.dagster_run.job_name} failed!",
            f"Run ID: {context.dagster_run.run_id}",
            f"Error: {context.failure_event.message}",
        ]
    )


def make_teams_on_run_failure_sensor(
    hook_url: str,
    message_fn: Callable[[RunFailureSensorContext], str] = _default_failure_message,
    http_proxy: Optional[str] = None,
    https_proxy: Optional[str] = None,
    timeout: Optional[float] = 60,
    verify: Optional[bool] = None,
    name: Optional[str] = None,
    dagit_base_url: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    monitored_jobs: Optional[
        List[
            Union[
                PipelineDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
            ]
        ]
    ] = None,
    monitor_all_repositories: bool = False,
):
    """Create a sensor on run failures that will message the given MS Teams webhook URL.

    Args:
        hook_url (str): MS Teams incoming webhook URL.
        message_fn (Optional(Callable[[RunFailureSensorContext], str])): Function which
            takes in the ``RunFailureSensorContext`` and outputs the message you want to send.
            Defaults to a text message that contains error message, job name, and run ID.
        http_proxy : (Optional[str]): Proxy for requests using http protocol.
        https_proxy : (Optional[str]): Proxy for requests using https protocol.
        timeout: (Optional[float]): Connection timeout in seconds. Defaults to 60.
        verify: (Optional[bool]): Whether to verify the servers TLS certificate.
        name: (Optional[str]): The name of the sensor. Defaults to "teams_on_run_failure".
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the failed run.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
        monitored_jobs (Optional[List[Union[PipelineDefinition, GraphDefinition, UnresolvedAssetJobDefinition, RepositorySelector, JobSelector]]]):
            Jobs in the current repository that will be monitored by this sensor. Defaults to None,
            which means the alert will be sent when any job in the repository matches the requested
            run_status. To monitor jobs in external repositories, use RepositorySelector and JobSelector.
        monitor_all_repositories (bool): If set to True, the sensor will monitor all runs in the
            Dagster instance. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.

    Examples:

        .. code-block:: python

            teams_on_run_failure = make_teams_on_run_failure_sensor(
                hook_url=os.getenv("TEAMS_WEBHOOK_URL")
            )

            @repository
            def my_repo():
                return [my_job + teams_on_run_failure]

        .. code-block:: python

            def my_message_fn(context: RunFailureSensorContext) -> str:
                return "Job {job_name} failed! Error: {error}".format(
                    job_name=context.dagster_run.job_name,
                    error=context.failure_event.message,
                )

            teams_on_run_failure = make_teams_on_run_failure_sensor(
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

    @run_failure_sensor(
        name=name,
        default_status=default_status,
        monitored_jobs=monitored_jobs,
        monitor_all_repositories=monitor_all_repositories,
    )
    def teams_on_run_failure(context: RunFailureSensorContext):

        text = message_fn(context)
        if dagit_base_url:
            text += "<a href='{base_url}/instance/runs/{run_id}'>View in Dagit</a>".format(
                base_url=dagit_base_url,
                run_id=context.dagster_run.run_id,
            )
        card = Card()
        card.add_attachment(text_message=text)
        teams_client.post_message(payload=card.payload)

    return teams_on_run_failure
