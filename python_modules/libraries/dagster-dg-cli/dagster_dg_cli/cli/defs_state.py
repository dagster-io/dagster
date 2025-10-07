import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

import click
from dagster_dg_core.utils import exit_with_error
from dagster_shared.record import record, replace

if TYPE_CHECKING:
    from dagster._core.storage.defs_state.base import DefsStateStorage
    from dagster.components.component.state_backed_component import StateBackedComponent
    from dagster.components.core.component_tree import ComponentTree
    from dagster_shared.serdes.objects.models import DefsStateInfo


@record
class ComponentStateRefreshStatus:
    status: Literal["refreshing", "done", "failed"]
    error: Optional[Exception] = None
    # For updating: start_time tracks when it began
    # For completed: duration tracks final elapsed time
    start_time: float = 0.0
    duration: Optional[float] = None

    @staticmethod
    def default() -> "ComponentStateRefreshStatus":
        return ComponentStateRefreshStatus(status="refreshing", start_time=time.time())


def raise_component_state_refresh_errors(statuses: dict[str, ComponentStateRefreshStatus]) -> None:
    """Raises an error if any of the component state refreshes failed."""
    errors = [
        (key, status.error)
        for key, status in statuses.items()
        if status.status == "failed" and status.error
    ]

    if errors:
        click.echo("\n" + click.style("Detailed error information:", fg="red", bold=True))
        for key, error in errors:
            click.echo(
                f"  {click.style(key, fg='white', bold=True)}: {click.style(str(error), fg='red')}"
            )

        raise errors[0][1]


def _get_components_to_refresh(
    component_tree: "ComponentTree", defs_state_keys: Optional[set[str]]
) -> list["StateBackedComponent"]:
    from dagster.components.component.state_backed_component import StateBackedComponent

    state_backed_components = component_tree.get_all_components(of_type=StateBackedComponent)
    if defs_state_keys is None:
        return state_backed_components

    selected_components = [
        component
        for component in state_backed_components
        if component.get_defs_state_key() in defs_state_keys
    ]
    missing_defs_keys = defs_state_keys - {
        component.get_defs_state_key() for component in selected_components
    }
    if missing_defs_keys:
        click.echo("Error: The following defs state keys were not found:")
        for key in sorted(missing_defs_keys):
            click.echo(f"  {key}")
        click.echo("Available defs state keys:")
        for key in sorted(
            [component.get_defs_state_key() for component in state_backed_components]
        ):
            click.echo(f"  {key}")
        exit_with_error("One or more specified defs state keys were not found.")
    return selected_components


async def _refresh_state_for_component(
    component: "StateBackedComponent", statuses: dict[str, ComponentStateRefreshStatus]
) -> None:
    """Refreshes the state of a component and tracks its state in the statuses dictionary as it progresses."""
    key = component.get_defs_state_key()

    try:
        await component.refresh_state()
        error = None
    except Exception as e:
        error = e

    statuses[key] = replace(
        statuses[key],
        duration=time.time() - statuses[key].start_time,
        status="done" if error is None else "failed",
        error=error,
    )


async def _refresh_state_for_components(
    defs_state_storage: "DefsStateStorage",
    components: list["StateBackedComponent"],
    statuses: dict[str, ComponentStateRefreshStatus],
) -> Optional["DefsStateInfo"]:
    await asyncio.gather(
        *[_refresh_state_for_component(component, statuses) for component in components]
    )
    return defs_state_storage.get_latest_defs_state_info()


def get_updated_defs_state_info_task_and_statuses(
    project_path: Path,
    defs_state_storage: "DefsStateStorage",
    defs_state_keys: Optional[set[str]] = None,
) -> tuple[asyncio.Task[Optional["DefsStateInfo"]], dict[str, ComponentStateRefreshStatus]]:
    """Creates an asyncio.Task that will refresh the defs state for all selected components within the specified project path.

    Can be used in place of `get_updated_defs_state_info_and_statuses` in cases where the caller wants to do other work
    (e.g. display progress) while the task is running.
    """
    from dagster.components.core.component_tree import ComponentTree
    from dagster_shared.utils.warnings import disable_dagster_warnings

    with disable_dagster_warnings():
        component_tree = ComponentTree.for_project(project_path)
        components_to_refresh = _get_components_to_refresh(component_tree, defs_state_keys)

    # shared dictionary to be used for all subtasks
    statuses = {
        component.get_defs_state_key(): ComponentStateRefreshStatus(
            status="refreshing", start_time=time.time()
        )
        for component in components_to_refresh
    }
    refresh_task = asyncio.create_task(
        _refresh_state_for_components(defs_state_storage, components_to_refresh, statuses)
    )
    return refresh_task, statuses


async def get_updated_defs_state_info_and_statuses(
    project_path: Path,
    defs_state_storage: "DefsStateStorage",
    defs_state_keys: Optional[set[str]] = None,
) -> tuple[Optional["DefsStateInfo"], dict[str, ComponentStateRefreshStatus]]:
    """Refreshes the defs state for all selected components within the specified project path,
    and returns the updated defs state info and statuses.
    """
    task, statuses = get_updated_defs_state_info_task_and_statuses(
        project_path, defs_state_storage, defs_state_keys
    )
    await task
    return task.result(), statuses
