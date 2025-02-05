from typing import Callable, Optional

from dagster._annotations import deprecated_param
from dagster._core.definitions import failure_hook, success_hook
from dagster._core.execution.context.hook import HookContext
from dagster._utils.warnings import normalize_renamed_param

from dagster_msteams.adaptive_card import AdaptiveCard
from dagster_msteams.card import Card
from dagster_msteams.resources import MSTeamsResource
from dagster_msteams.utils import MSTeamsHyperlink, build_message_with_link


def _default_status_message(context: HookContext, status: str) -> str:
    return f"Op {context.op.name} on job {context.job_name} {status}!\nRun ID: {context.run_id}"


def _default_failure_message(context: HookContext) -> str:
    return _default_status_message(context, status="failed")


def _default_success_message(context: HookContext) -> str:
    return _default_status_message(context, status="succeeded")


@deprecated_param(
    param="dagit_base_url",
    breaking_version="2.0",
    additional_warn_text="Use `webserver_base_url` instead.",
)
def teams_on_failure(
    message_fn: Callable[[HookContext], str] = _default_failure_message,
    dagit_base_url: Optional[str] = None,
    webserver_base_url: Optional[str] = None,
):
    """Create a hook on step failure events that will message the given MS Teams webhook URL.

    Args:
        message_fn (Optional(Callable[[HookContext], str])): Function which takes in the
            HookContext outputs the message you want to send.
        dagit_base_url: (Optional[str]): The base url of your webserver instance. Specify this
            to allow messages to include deeplinks to the specific run that triggered
            the hook.
        webserver_base_url: (Optional[str]): The base url of your webserver instance. Specify this
            to allow messages to include deeplinks to the specific run that triggered
            the hook.

    Examples:
        .. code-block:: python

            @teams_on_failure(webserver_base_url="http://localhost:3000")
            @job(...)
            def my_job():
                pass

        .. code-block:: python

            def my_message_fn(context: HookContext) -> str:
                return f"Op {context.op.name} failed!"

            @op
            def a_op(context):
                pass

            @job(...)
            def my_job():
                a_op.with_hooks(hook_defs={teams_on_failure("#foo", my_message_fn)})

    """
    webserver_base_url = normalize_renamed_param(
        webserver_base_url, "webserver_base_url", dagit_base_url, "dagit_base_url"
    )

    @failure_hook(required_resource_keys={"msteams"})
    def _hook(context: HookContext):
        if isinstance(context.resources.msteams, MSTeamsResource):
            client = context.resources.msteams.get_client()
        else:
            client = context.resources.msteams

        message = message_fn(context)
        link = (
            MSTeamsHyperlink("View in Dagster UI", f"{webserver_base_url}/runs/{context.run_id}")
            if webserver_base_url
            else None
        )
        card = Card() if client.is_legacy_webhook() else AdaptiveCard()
        card.add_attachment(build_message_with_link(client.is_legacy_webhook(), message, link))
        client.post_message(card.payload)

    return _hook


@deprecated_param(
    param="dagit_base_url",
    breaking_version="2.0",
    additional_warn_text="Use `webserver_base_url` instead.",
)
def teams_on_success(
    message_fn: Callable[[HookContext], str] = _default_success_message,
    dagit_base_url: Optional[str] = None,
    webserver_base_url: Optional[str] = None,
):
    """Create a hook on step success events that will message the given MS Teams webhook URL.

    Args:
        message_fn (Optional(Callable[[HookContext], str])): Function which takes in the
            HookContext outputs the message you want to send.
        dagit_base_url: (Optional[str]): The base url of your webserver instance. Specify this
            to allow messages to include deeplinks to the specific run that triggered
            the hook.

    Examples:
        .. code-block:: python

            @teams_on_success(webserver_base_url="http://localhost:3000")
            @job(...)
            def my_job():
                pass

        .. code-block:: python

            def my_message_fn(context: HookContext) -> str:
                return f"Op {context.op.name} failed!"

            @op
            def a_op(context):
                pass

            @job(...)
            def my_job():
                a_op.with_hooks(hook_defs={teams_on_success("#foo", my_message_fn)})

    """
    webserver_base_url = normalize_renamed_param(
        webserver_base_url, "webserver_base_url", dagit_base_url, "dagit_base_url"
    )

    @success_hook(required_resource_keys={"msteams"})
    def _hook(context: HookContext):
        if isinstance(context.resources.msteams, MSTeamsResource):
            client = context.resources.msteams.get_client()
        else:
            client = context.resources.msteams

        message = message_fn(context)
        link = (
            MSTeamsHyperlink("View in Dagster UI", f"{webserver_base_url}/runs/{context.run_id}")
            if webserver_base_url
            else None
        )
        card = Card() if client.is_legacy_webhook() else AdaptiveCard()
        card.add_attachment(build_message_with_link(client.is_legacy_webhook(), message, link))
        client.post_message(card.payload)

    return _hook
