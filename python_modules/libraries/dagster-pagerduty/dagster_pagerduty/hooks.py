from typing import Callable, Optional

from dagster.core.definitions import failure_hook
from dagster.core.execution.context.system import HookContext


def _default_summary_fn(context: HookContext) -> str:
    return "Solid {solid_name} on pipeline {pipeline_name} failed!".format(
        solid_name=context.solid.name,
        pipeline_name=context.pipeline_name,
    )


def _dedup_key_fn(context: HookContext) -> str:
    return "{pipeline_name}|{solid_name}".format(
        pipeline_name=context.pipeline_name,
        solid_name=context.solid.name,
    )


def _source_fn(context: HookContext):
    return "{pipeline_name}".format(pipeline_name=context.pipeline_name)


def pagerduty_on_failure(
    severity: str,
    summary_fn: Callable[[HookContext], str] = _default_summary_fn,
    dagit_base_url: Optional[str] = None,
):
    """Create a hook on step failure events that will trigger a PagerDuty alert.

    Args:
        severity (str): How impacted the affected system is. Displayed to users in lists and
            influences the priority of any created incidents. Must be one of {info, warning, error, critical}
        summary_fn (Optional(Callable[[HookContext], str])): Function which takes in the HookContext
            outputs a summary of the issue.
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            alerts to include deeplinks to the specific pipeline run that triggered the hook.

    Examples:
        .. code-block:: python

            @pagerduty_on_failure("info", dagit_base_url="http://localhost:3000")
            @pipeline(...)
            def my_pipeline():
                pass

        .. code-block:: python

            def my_summary_fn(context: HookContext) -> str:
                return "Solid {solid_name} failed!".format(
                    solid_name=context.solid
                )

            @solid
            def a_solid(context):
                pass

            @pipeline(...)
            def my_pipeline():
                a_solid.with_hooks(hook_defs={pagerduty_on_failure(severity="critical", summary_fn=my_summary_fn)})

    """

    @failure_hook(required_resource_keys={"pagerduty"})
    def _hook(context: HookContext):
        custom_details = {}
        if dagit_base_url:
            custom_details = {
                "dagit url": "{base_url}/instance/runs/{run_id}".format(
                    base_url=dagit_base_url, run_id=context.run_id
                )
            }
        context.resources.pagerduty.EventV2_create(
            summary=summary_fn(context),
            source=_source_fn(context),
            severity=severity,
            dedup_key=_dedup_key_fn(context),
            custom_details=custom_details,
        )

    return _hook
