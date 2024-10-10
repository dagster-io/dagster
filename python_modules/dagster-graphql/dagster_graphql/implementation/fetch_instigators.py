from typing import TYPE_CHECKING, Optional, Union

import dagster._check as check
from dagster._core.definitions.instigation_logger import get_instigation_log_records
from dagster._core.definitions.selector import InstigatorSelector
from dagster._core.log_manager import LOG_RECORD_METADATA_ATTR
from dagster._core.remote_representation.external import CompoundID
from dagster._core.scheduler.instigation import InstigatorStatus

if TYPE_CHECKING:
    from dagster_graphql.schema.instigation import (
        GrapheneInstigationEventConnection,
        GrapheneInstigationState,
        GrapheneInstigationStateNotFoundError,
    )
    from dagster_graphql.schema.util import ResolveInfo


def get_instigator_state_by_selector(
    graphene_info: "ResolveInfo",
    selector: InstigatorSelector,
    instigator_id: Optional[CompoundID],
) -> Union["GrapheneInstigationState", "GrapheneInstigationStateNotFoundError"]:
    from dagster_graphql.schema.instigation import (
        GrapheneInstigationState,
        GrapheneInstigationStateNotFoundError,
    )

    check.inst_param(selector, "selector", InstigatorSelector)

    if instigator_id:
        state = graphene_info.context.instance.get_instigator_state(
            origin_id=instigator_id.remote_origin_id,
            selector_id=instigator_id.selector_id,
        )
        # if the state tells us the status on its own short cut and return it
        # if its declared in code we need the full snapshot to resolve
        if state and state.status in (InstigatorStatus.STOPPED, InstigatorStatus.RUNNING):
            return GrapheneInstigationState(state)

    location = graphene_info.context.get_code_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    if repository.has_sensor(selector.name):
        sensor = repository.get_sensor(selector.name)
        stored_state = graphene_info.context.instance.get_instigator_state(
            sensor.get_remote_origin_id(),
            sensor.selector_id,
        )
        current_state = sensor.get_current_instigator_state(stored_state)
    elif repository.has_schedule(selector.name):
        schedule = repository.get_schedule(selector.name)
        stored_state = graphene_info.context.instance.get_instigator_state(
            schedule.get_remote_origin_id(),
            schedule.selector_id,
        )
        current_state = schedule.get_current_instigator_state(stored_state)
    else:
        return GrapheneInstigationStateNotFoundError(selector.name)

    return GrapheneInstigationState(current_state)


def get_instigation_states_by_repository_id(
    graphene_info: "ResolveInfo",
    repository_id: CompoundID,
):
    from dagster_graphql.schema.instigation import (
        GrapheneInstigationState,
        GrapheneInstigationStates,
    )

    states = graphene_info.context.instance.all_instigator_state(
        repository_origin_id=repository_id.remote_origin_id,
        repository_selector_id=repository_id.selector_id,
    )

    return GrapheneInstigationStates(results=[GrapheneInstigationState(state) for state in states])


def get_tick_log_events(graphene_info: "ResolveInfo", tick) -> "GrapheneInstigationEventConnection":
    from dagster_graphql.schema.instigation import (
        GrapheneInstigationEvent,
        GrapheneInstigationEventConnection,
    )
    from dagster_graphql.schema.logs.log_level import GrapheneLogLevel

    if not tick.log_key:
        return GrapheneInstigationEventConnection(events=[], cursor="", hasMore=False)

    records = get_instigation_log_records(graphene_info.context.instance, tick.log_key)

    events = []
    for record_dict in records:
        exc_info = record_dict.get("exc_info")
        message = record_dict[LOG_RECORD_METADATA_ATTR]["orig_message"]
        if exc_info:
            message = f"{message}\n\n{exc_info}"

        event = GrapheneInstigationEvent(
            message=message,
            level=GrapheneLogLevel.from_level(record_dict["levelno"]),
            timestamp=int(record_dict["created"] * 1000),
        )

        events.append(event)

    return GrapheneInstigationEventConnection(
        events=events,
        cursor=None,
        hasMore=False,
    )
