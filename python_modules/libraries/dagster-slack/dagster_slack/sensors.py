from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from dagster import (
    AssetSelection,
    DefaultSensorStatus,
    FreshnessPolicySensorContext,
    freshness_policy_sensor,
)
from dagster._annotations import deprecated_param, experimental
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

T = TypeVar("T", RunFailureSensorContext, FreshnessPolicySensorContext)


def _build_slack_blocks_and_text(
    context: T,
    text_fn: Callable[[T], str],
    blocks_fn: Optional[Callable[[T], List[Dict[Any, Any]]]],
    webserver_base_url: Optional[str],
) -> Tuple[List[Dict[str, Any]], str]:
    main_body_text = text_fn(context)
    blocks: List[Dict[Any, Any]] = []
    if blocks_fn:
        blocks.extend(blocks_fn(context))
    else:
        if isinstance(context, RunFailureSensorContext):
            text = (
                f'*Job "{context.dagster_run.job_name}" failed.'
                f' `{context.dagster_run.run_id.split("-")[0]}`*'
            )
        else:
            text = (
                f'*Asset "{context.asset_key.to_user_string()}" is now'
                f' {"on time" if context.minutes_overdue == 0 else f"{context.minutes_overdue:.2f} minutes late.*"}'
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
        if isinstance(context, RunFailureSensorContext):
            url = f"{webserver_base_url}/runs/{context.dagster_run.run_id}"
        else:
            url = f"{webserver_base_url}/assets/{'/'.join(context.asset_key.path)}"
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
def make_slack_on_run_failure_sensor(
    channel: str,
    slack_token: str,
    text_fn: Callable[[RunFailureSensorContext], str] = _default_failure_message_text_fn,
    blocks_fn: Optional[Callable[[RunFailureSensorContext], List[Dict[Any, Any]]]] = None,
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
    monitor_all_repositories: bool = False,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    webserver_base_url: Optional[str] = None,
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
        monitor_all_repositories (bool): If set to True, the sensor will monitor all runs in the
            Dagster instance. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
        webserver_base_url: (Optional[str]): The base url of your webserver instance. Specify this to allow
            messages to include deeplinks to the failed job run.

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

    @run_failure_sensor(
        name=name,
        minimum_interval_seconds=minimum_interval_seconds,
        monitored_jobs=jobs,
        monitor_all_repositories=monitor_all_repositories,
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


def _default_freshness_message_text_fn(context: FreshnessPolicySensorContext) -> str:
    return (
        f"Asset `{context.asset_key.to_user_string()}` is now {context.minutes_overdue:.2f} minutes"
        " late."
    )


@deprecated_param(
    param="dagit_base_url",
    breaking_version="2.0",
    additional_warn_text="Use `webserver_base_url` instead.",
)
@experimental
def make_slack_on_freshness_policy_status_change_sensor(
    channel: str,
    slack_token: str,
    asset_selection: AssetSelection,
    warn_after_minutes_overdue: float = 0,
    notify_when_back_on_time: bool = False,
    text_fn: Callable[[FreshnessPolicySensorContext], str] = _default_freshness_message_text_fn,
    blocks_fn: Optional[Callable[[FreshnessPolicySensorContext], List[Dict[Any, Any]]]] = None,
    name: Optional[str] = None,
    dagit_base_url: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    webserver_base_url: Optional[str] = None,
):
    """Create a sensor that will message the given Slack channel whenever an asset in the provided
    AssetSelection becomes out of date. Messages are only fired when the state changes, meaning
    only a single slack message will be sent (when the asset begins to be out of date). If
    `notify_when_back_on_time` is set to `True`, a second slack message will be sent once the asset
    is on time again.

    Args:
        channel (str): The channel to send the message to (e.g. "#my_channel")
        slack_token (str): The slack token.
            Tokens are typically either user tokens or bot tokens. More in the Slack API
            documentation here: https://api.slack.com/docs/token-types
        asset_selection (AssetSelection): The selection of assets which this sensor will monitor.
            Alerts will only be fired for assets that have a FreshnessPolicy defined.
        warn_after_minutes_overdue (float): How many minutes past the specified FreshnessPolicy this
            sensor will wait before firing an alert (by default, an alert will be fired as soon as
            the policy is violated).
        notify_when_back_on_time (bool): If a success message should be sent when the asset becomes on
            time again.
        text_fn (Optional(Callable[[RunFailureSensorContext], str])): Function which
            takes in the ``FreshnessPolicySensorContext`` and outputs the message you want to send.
            Defaults to a text message that contains the relevant asset key, and the number of
            minutes past its defined freshness policy it currently is.
            The usage of the `text_fn` changes depending on whether you're using `blocks_fn`. If you
            are using `blocks_fn`, this is used as a fallback string to display in notifications. If
            you aren't, this is the main body text of the message. It can be formatted as plain text,
            or with markdown.
            See more details in https://api.slack.com/methods/chat.postMessage#text_usage
        blocks_fn (Callable[[FreshnessPolicySensorContext], List[Dict]]): Function which takes in
            the ``FreshnessPolicySensorContext`` and outputs the message blocks you want to send.
            See information about Blocks in https://api.slack.com/reference/block-kit/blocks
        name: (Optional[str]): The name of the sensor. Defaults to "slack_on_freshness_policy".
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the relevant asset page.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
        webserver_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the relevant asset page.

    Examples:
        .. code-block:: python

            slack_on_freshness_policy = make_slack_on_freshness_policy_status_change_sensor(
                "#my_channel",
                os.getenv("MY_SLACK_TOKEN"),
            )

        .. code-block:: python

            def my_message_fn(context: FreshnessPolicySensorContext) -> str:
                if context.minutes_overdue == 0:
                    return f"Asset {context.asset_key} is currently on time :)"
                return (
                    f"Asset {context.asset_key} is currently {context.minutes_overdue} minutes late!!"
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

    @freshness_policy_sensor(
        name=name, asset_selection=asset_selection, default_status=default_status
    )
    def slack_on_freshness_policy(context: FreshnessPolicySensorContext):
        if context.minutes_overdue is None or context.previous_minutes_overdue is None:
            return

        if (
            context.minutes_overdue > warn_after_minutes_overdue
            and context.previous_minutes_overdue <= warn_after_minutes_overdue
        ) or (
            notify_when_back_on_time
            and context.minutes_overdue == 0
            and context.previous_minutes_overdue != 0
        ):
            blocks, main_body_text = _build_slack_blocks_and_text(
                context=context,
                text_fn=text_fn,
                blocks_fn=blocks_fn,
                webserver_base_url=webserver_base_url,
            )

            slack_client.chat_postMessage(channel=channel, blocks=blocks, text=main_body_text)

    return slack_on_freshness_policy
