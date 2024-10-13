from typing import Callable, Optional

from dagster._annotations import deprecated_param
from dagster._core.definitions import failure_hook
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.execution.context.hook import HookContext
from dagster._utils.warnings import normalize_renamed_param


def _default_summary_fn(context: HookContext) -> str:
    return f"Op {context.op.name} on job {context.job_name} failed!"


def _dedup_key_fn(context: HookContext) -> str:
    return f"{context.job_name}|{context.op.name}"


def _source_fn(context: HookContext) -> str:
    return f"{context.job_name}"


@deprecated_param(
    param="dagit_base_url",
    breaking_version="2.0",
    additional_warn_text="Use `webserver_base_url` instead.",
)
def pagerduty_on_failure(
    severity: str,
    summary_fn: Callable[[HookContext], str] = _default_summary_fn,
    dagit_base_url: Optional[str] = None,
    webserver_base_url: Optional[str] = None,
) -> HookDefinition:
    """Create a hook on step failure events that will trigger a PagerDuty alert.

    Args:
        severity (str): How impacted the affected system is. Displayed to users in lists and
            influences the priority of any created incidents. Must be one of {info, warning, error, critical}
        summary_fn (Optional(Callable[[HookContext], str])): Function which takes in the HookContext
            outputs a summary of the issue.
        dagit_base_url: (Optional[str]): The base url of your webserver instance. Specify this to allow
            alerts to include deeplinks to the specific run that triggered the hook.
        webserver_base_url: (Optional[str]): The base url of your webserver instance. Specify this to allow
            alerts to include deeplinks to the specific run that triggered the hook.

    Examples:
        .. code-block:: python
            @op
            def my_op(context):
                pass

            @job(
                resource_defs={"pagerduty": pagerduty_resource},
                hooks={pagerduty_on_failure("info", webserver_base_url="http://localhost:3000")},
            )
            def my_job():
                my_op()

        .. code-block:: python

            def my_summary_fn(context: HookContext) -> str:
                return f"Op {context.op.name} failed!"

            @op
            def my_op(context):
                pass

            @job(resource_defs={"pagerduty": pagerduty_resource})
            def my_job():
                my_op.with_hooks(hook_defs={pagerduty_on_failure(severity="critical", summary_fn=my_summary_fn)})

    """
    webserver_base_url = normalize_renamed_param(
        webserver_base_url, "webserver_base_url", dagit_base_url, "dagit_base_url"
    )

    @failure_hook(required_resource_keys={"pagerduty"})
    def _hook(context: HookContext):
        custom_details = {}
        if webserver_base_url:
            custom_details = {"webserver url": f"{webserver_base_url}/runs/{context.run_id}"}
        context.resources.pagerduty.EventV2_create(
            summary=summary_fn(context),
            source=_source_fn(context),
            severity=severity,
            dedup_key=_dedup_key_fn(context),
            custom_details=custom_details,
        )

    return _hook
