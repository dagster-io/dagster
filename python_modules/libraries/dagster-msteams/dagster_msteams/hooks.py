from typing import Callable, Optional

from dagster.core.definitions import failure_hook, success_hook
from dagster.core.execution.context.hook import HookContext

from dagster_msteams.card import Card


def _default_status_message(context: HookContext, status: str) -> str:
    return "Solid {solid_name} on pipeline {pipeline_name} {status}!\nRun ID: {run_id}".format(
        solid_name=context.solid.name,
        pipeline_name=context.pipeline_name,
        run_id=context.run_id,
        status=status,
    )


def _default_failure_message(context: HookContext) -> str:
    return _default_status_message(context, status="failed")


def _default_success_message(context: HookContext) -> str:
    return _default_status_message(context, status="succeeded")


def teams_on_failure(
    message_fn: Callable[[HookContext], str] = _default_failure_message,
    dagit_base_url: Optional[str] = None,
):
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
        context.resources.msteams.post_message(payload=card.payload)

    return _hook


def teams_on_success(
    message_fn: Callable[[HookContext], str] = _default_success_message,
    dagit_base_url: Optional[str] = None,
):
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
        context.resources.msteams.post_message(payload=card.payload)

    return _hook
