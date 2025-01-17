from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from dagster import DefaultSensorStatus
from dagster._annotations import deprecated_param
from dagster._core.definitions import GraphDefinition, JobDefinition
from dagster._core.definitions.run_status_sensor_definition import (
    RunFailureSensorContext,
    run_failure_sensor,
)
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._utils.warnings import normalize_renamed_param
from slack_sdk.web.client import WebClient

if TYPE_CHECKING:
    from dagster._core.definitions.selector import (
        CodeLocationSelector,
        JobSelector,
        RepositorySelector,
    )


def _build_slack_blocks_and_text(
    context: RunFailureSensorContext,
    text_fn: Callable[[RunFailureSensorContext], str],
    blocks_fn: Optional[Callable[[RunFailureSensorContext], list[dict[Any, Any]]]],
    webserver_base_url: Optional[str],
) -> tuple[list[dict[str, Any]], str]:
    main_body_text = text_fn(context)
    blocks: list[dict[Any, Any]] = []
    if blocks_fn:
        blocks.extend(blocks_fn(context))
    else:
        text = (
            f'*Job "{context.dagster_run.job_name}" failed.'
            f' `{context.dagster_run.run_id.split("-")[0]}`*'
        )

        blocks.extend(
            [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text,
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": main_body_text},
                },
            ]
        )

    if webserver_base_url:
        url = f"{webserver_base_url}/runs/{context.dagster_run.run_id}"
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in Dagster UI"},
                        "url": url,
                    }
                ],
            }
        )
    return blocks, main_body_text


def _default_failure_message_text_fn(context: RunFailureSensorContext) -> str:
    return f"Error: ```{context.failure_event.message}```"


@deprecated_param(
    param="dagit_base_url",
    breaking_version="2.0",
    additional_warn_text="Use `webserver_base_url` instead.",
)
@deprecated_param(
    param="job_selection",
    breaking_version="2.0",
    additional_warn_text="Use `monitored_jobs` instead.",
)
@deprecated_param(
    param="monitor_all_repositories",
    breaking_version="2.0",
    additional_warn_text="Use `monitor_all_code_locations` instead.",
)
def make_slack_on_run_failure_sensor(
    channel: str,
    slack_token: str,
    text_fn: Callable[[RunFailureSensorContext], str] = _default_failure_message_text_fn,
    blocks_fn: Optional[Callable[[RunFailureSensorContext], list[dict[Any, Any]]]] = None,
    name: Optional[str] = None,
    dagit_base_url: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    monitored_jobs: Optional[
        Sequence[
            Union[
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
                "CodeLocationSelector",
            ]
        ]
    ] = None,
    job_selection: Optional[
        Sequence[
            Union[
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
                "CodeLocationSelector",
            ]
        ]
    ] = None,
    monitor_all_code_locations: bool = False,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    webserver_base_url: Optional[str] = None,
    monitor_all_repositories: bool = False,
):
    """Create a sensor on job failures that will message the given Slack channel.

    Args:
        channel (str): The channel to send the message to (e.g. "#my_channel")
        slack_token (str): The slack token.
            Tokens are typically either user tokens or bot tokens. More in the Slack API
            documentation here: https://api.slack.com/docs/token-types
        text_fn (Optional(Callable[[RunFailureSensorContext], str])): Function which
            takes in the ``RunFailureSensorContext`` and outputs the message you want to send.
            Defaults to a text message that contains error message, job name, and run ID.
            The usage of the `text_fn` changes depending on whether you're using `blocks_fn`. If you
            are using `blocks_fn`, this is used as a fallback string to display in notifications. If
            you aren't, this is the main body text of the message. It can be formatted as plain text,
            or with markdown.
            See more details in https://api.slack.com/methods/chat.postMessage#text_usage
        blocks_fn (Callable[[RunFailureSensorContext], List[Dict]]): Function which takes in
            the ``RunFailureSensorContext`` and outputs the message blocks you want to send.
            See information about Blocks in https://api.slack.com/reference/block-kit/blocks
        name: (Optional[str]): The name of the sensor. Defaults to "slack_on_run_failure".
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the failed job run.
        minimum_interval_seconds: (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        monitored_jobs (Optional[List[Union[JobDefinition, GraphDefinition, RepositorySelector, JobSelector, CodeLocationSensor]]]): The jobs in the
            current repository that will be monitored by this failure sensor. Defaults to None, which
            means the alert will be sent when any job in the repository fails. To monitor jobs in external repositories, use RepositorySelector and JobSelector
        job_selection (Optional[List[Union[JobDefinition, GraphDefinition, RepositorySelector, JobSelector, CodeLocationSensor]]]): (deprecated in favor of monitored_jobs)
            The jobs in the current repository that will be monitored by this failure sensor. Defaults to None, which means the alert will
            be sent when any job in the repository fails.
        monitor_all_code_locations (bool): If set to True, the sensor will monitor all runs in the
            Dagster deployment. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
        webserver_base_url: (Optional[str]): The base url of your webserver instance. Specify this to allow
            messages to include deeplinks to the failed job run.
        monitor_all_repositories (bool): If set to True, the sensor will monitor all runs in the
            Dagster instance. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.

    Examples:
        .. code-block:: python

            slack_on_run_failure = make_slack_on_run_failure_sensor(
                "#my_channel",
                os.getenv("MY_SLACK_TOKEN")
            )

            @repository
            def my_repo():
                return [my_job + slack_on_run_failure]

        .. code-block:: python

            def my_message_fn(context: RunFailureSensorContext) -> str:
                return (
                    f"Job {context.dagster_run.job_name} failed!"
                    f"Error: {context.failure_event.message}"
                )

            slack_on_run_failure = make_slack_on_run_failure_sensor(
                channel="#my_channel",
                slack_token=os.getenv("MY_SLACK_TOKEN"),
                text_fn=my_message_fn,
                webserver_base_url="http://mycoolsite.com",
            )


    """
    webserver_base_url = normalize_renamed_param(
        webserver_base_url, "webserver_base_url", dagit_base_url, "dagit_base_url"
    )
    slack_client = WebClient(token=slack_token)
    jobs = monitored_jobs if monitored_jobs else job_selection
    monitor_all = monitor_all_code_locations or monitor_all_repositories

    @run_failure_sensor(
        name=name,
        minimum_interval_seconds=minimum_interval_seconds,
        monitored_jobs=jobs,
        monitor_all_code_locations=monitor_all,
        default_status=default_status,
    )
    def slack_on_run_failure(context: RunFailureSensorContext):
        blocks, main_body_text = _build_slack_blocks_and_text(
            context=context,
            text_fn=text_fn,
            blocks_fn=blocks_fn,
            webserver_base_url=webserver_base_url,
        )

        slack_client.chat_postMessage(channel=channel, blocks=blocks, text=main_body_text)

    return slack_on_run_failure
