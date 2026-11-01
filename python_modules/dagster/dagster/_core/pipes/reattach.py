import logging
import time
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from dagster._core.definitions.metadata import MetadataValue, TextMetadataValue
from dagster._core.events import DagsterEventType, EngineEventData
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import ASSET_RESUME_RETRY_TAG, RESUME_RETRY_TAG
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value, whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
    from dagster._core.execution.context.op_execution_context import OpExecutionContext
    from dagster._core.instance import DagsterInstance

_logger = logging.getLogger(__name__)

PIPES_LAUNCH_HANDLE_METADATA_KEY = "dagster_pipes/launch_handle"
EXTERNAL_RUN_URL_METADATA_KEY = "external run url"

# Guard against pathological parent_run_id chains.
_MAX_ANCESTRY_DEPTH = 64


@whitelist_for_serdes
@record
class PipesLaunchHandle:
    """Durable record of an external run launched by a pipes client.

    Written to the event log at launch so that a later execution of the same step (step
    retry, resumed run worker, or run-level retry) can find the in-flight external run
    and reattach to it instead of launching a duplicate.
    """

    client_name: str
    external_run_id: str
    step_key: str
    retry_number: int
    launched_at: float
    external_run_url: str | None = None
    extras: Mapping[str, Any] = {}


def record_external_launch(
    context: "OpExecutionContext | AssetExecutionContext",
    *,
    client_name: str,
    external_run_id: str,
    external_run_url: str | None = None,
    extras: Mapping[str, Any] | None = None,
) -> PipesLaunchHandle:
    """Persist a :py:class:`PipesLaunchHandle` for the current step as an engine event.

    Call immediately after starting the external run, before polling it.
    """
    step_key = context.get_step_execution_context().step.key
    handle = PipesLaunchHandle(
        client_name=client_name,
        external_run_id=external_run_id,
        step_key=step_key,
        retry_number=context.retry_number,
        launched_at=time.time(),
        external_run_url=external_run_url,
        extras=dict(extras) if extras else {},
    )
    _report_handle_event(
        context, handle, f"[pipes] Launched external run {external_run_id} via {client_name}."
    )
    return handle


def record_external_reattach(
    context: "OpExecutionContext | AssetExecutionContext",
    handle: PipesLaunchHandle,
) -> PipesLaunchHandle:
    """Persist a reattachment to a previously launched external run.

    Re-emits the handle (with the current retry number) so the freshest handle lives in
    the current run's event log, and the launch → reattach chain is auditable.
    """
    updated = PipesLaunchHandle(
        client_name=handle.client_name,
        external_run_id=handle.external_run_id,
        step_key=context.get_step_execution_context().step.key,
        retry_number=context.retry_number,
        launched_at=handle.launched_at,
        external_run_url=handle.external_run_url,
        extras=handle.extras,
    )
    _report_handle_event(
        context,
        updated,
        f"[pipes] Reattached to in-progress external run {handle.external_run_id} via"
        f" {handle.client_name}.",
    )
    return updated


def _report_handle_event(
    context: "OpExecutionContext | AssetExecutionContext",
    handle: PipesLaunchHandle,
    message: str,
) -> None:
    metadata: dict[str, MetadataValue] = {
        PIPES_LAUNCH_HANDLE_METADATA_KEY: MetadataValue.text(serialize_value(handle))
    }
    if handle.external_run_url:
        metadata[EXTERNAL_RUN_URL_METADATA_KEY] = MetadataValue.url(handle.external_run_url)
    context.instance.report_engine_event(
        message,
        dagster_run=context.dagster_run,
        engine_event_data=EngineEventData(metadata=metadata),
        step_key=handle.step_key,
    )


def find_latest_launch_handle(
    context: "OpExecutionContext | AssetExecutionContext",
    *,
    client_name: str,
) -> PipesLaunchHandle | None:
    """Find the most recent launch handle recorded by `client_name` for the current step.

    Searches the current run's event log first (covering step retries and resumed run
    workers), then walks the parent run chain — but only across from-failure retries, so
    that an intentional re-execution (e.g. all steps) launches fresh instead of adopting
    the prior execution's external run.

    Suggested client policy: reattach when the external run is still in progress or
    succeeded; launch fresh when it terminally failed (a retry exists to re-execute) or
    when no handle is found.
    """
    return find_latest_launch_handle_for_run(
        instance=context.instance,
        run=context.dagster_run,
        step_key=context.get_step_execution_context().step.key,
        client_name=client_name,
    )


def find_latest_launch_handle_for_run(
    *,
    instance: "DagsterInstance",
    run: DagsterRun,
    step_key: str,
    client_name: str,
) -> PipesLaunchHandle | None:
    current: DagsterRun | None = run
    seen: set[str] = set()
    while current and current.run_id not in seen and len(seen) < _MAX_ANCESTRY_DEPTH:
        seen.add(current.run_id)
        handle = _latest_handle_in_run(instance, current.run_id, step_key, client_name)
        if handle:
            return handle
        if not _is_from_failure_retry(current):
            return None
        current = instance.get_run_by_id(current.parent_run_id) if current.parent_run_id else None
    return None


def _is_from_failure_retry(run: DagsterRun) -> bool:
    return (
        run.tags.get(RESUME_RETRY_TAG) == "true" or run.tags.get(ASSET_RESUME_RETRY_TAG) == "true"
    )


def _latest_handle_in_run(
    instance: "DagsterInstance", run_id: str, step_key: str, client_name: str
) -> PipesLaunchHandle | None:
    entries = instance.all_logs(run_id, of_type=DagsterEventType.ENGINE_EVENT)
    for entry in reversed(entries):
        if entry.step_key != step_key or entry.dagster_event is None:
            continue
        metadata = entry.dagster_event.engine_event_data.metadata
        value = metadata.get(PIPES_LAUNCH_HANDLE_METADATA_KEY)
        if not isinstance(value, TextMetadataValue) or value.value is None:
            continue
        try:
            handle = deserialize_value(value.value, PipesLaunchHandle)
        except Exception:
            # An unreadable handle (e.g. written by a different dagster version) must
            # not cause the step to fail.
            _logger.warning("Ignoring unreadable launch handle in run %s", run_id, exc_info=True)
            continue

        if handle.step_key == step_key and handle.client_name == client_name:
            return handle
    return None
