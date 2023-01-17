from typing import Callable, Optional

from dagster._core.definitions import failure_hook, success_hook
from dagster._core.execution.context.hook import HookContext

from dagster_msteams.card import Card


def _default_status_message(context: HookContext, status: str) -> str:
    return f"Op {context.op.name} on job {context.job_name} {status}!\nRun ID: {context.run_id}"


def _default_failure_message(context: HookContext) -> str:
    return _default_status_message(context, status="failed")


def _default_success_message(context: HookContext) -> str:
    return _default_status_message(context, status="succeeded")


def teams_on_failure(
    message_fn: Callable[[HookContext], str] = _default_failure_message,
    dagit_base_url: Optional[str] = None,
):
    """Create a hook on step failure events that will message the given MS Teams webhook URL.

    Args:
        message_fn (Optional(Callable[[HookContext], str])): Function which takes in the
            HookContext outputs the message you want to send.
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this
            to allow messages to include deeplinks to the specific run that triggered
            the hook.

    Examples:
        .. code-block:: python

            @teams_on_failure(dagit_base_url="http://localhost:3000")
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

    @failure_hook(required_resource_keys={"msteams"})
    def _hook(context: HookContext):
        text = message_fn(context)
        if dagit_base_url:
            text += "<a href='{base_url}/instance/runs/{run_id}'>View in Dagit</a>".format(
                base_url=dagit_base_url,
                run_id=context.run_id,
            )
        card = Card()
        card.add_attachment(text_message=text)
        context.resources.msteams.post_message(payload=card.payload)  # type: ignore

    return _hook


def teams_on_success(
    message_fn: Callable[[HookContext], str] = _default_success_message,
    dagit_base_url: Optional[str] = None,
):
    """Create a hook on step success events that will message the given MS Teams webhook URL.

    Args:
        message_fn (Optional(Callable[[HookContext], str])): Function which takes in the
            HookContext outputs the message you want to send.
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this
            to allow messages to include deeplinks to the specific run that triggered
            the hook.

    Examples:
        .. code-block:: python

            @teams_on_success(dagit_base_url="http://localhost:3000")
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

    @success_hook(required_resource_keys={"msteams"})
    def _hook(context: HookContext):
        text = message_fn(context)
        if dagit_base_url:
            text += "<a href='{base_url}/instance/runs/{run_id}'>View in Dagit</a>".format(
                base_url=dagit_base_url,
                run_id=context.run_id,
            )
        card = Card()
        card.add_attachment(text_message=text)
        context.resources.msteams.post_message(payload=card.payload)  # type: ignore

    return _hook
