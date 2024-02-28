from typing import TYPE_CHECKING, Union

import dagster._check as check
from dagster._core.definitions.instigation_logger import get_instigation_log_records
from dagster._core.definitions.selector import InstigatorSelector
from dagster._core.log_manager import LOG_RECORD_METADATA_ATTR

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo

    from ..schema.instigation import (
        GrapheneInstigationEventConnection,
        GrapheneInstigationState,
        GrapheneInstigationStateNotFoundError,
    )


def get_instigator_state_or_error(
    graphene_info: "ResolveInfo", selector: InstigatorSelector
) -> Union["GrapheneInstigationState", "GrapheneInstigationStateNotFoundError"]:
    from ..schema.instigation import GrapheneInstigationState, GrapheneInstigationStateNotFoundError

    check.inst_param(selector, "selector", InstigatorSelector)
    location = graphene_info.context.get_code_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    if repository.has_external_sensor(selector.name):
        external_sensor = repository.get_external_sensor(selector.name)
        stored_state = graphene_info.context.instance.get_instigator_state(
            external_sensor.get_external_origin_id(),
            external_sensor.selector_id,
        )
        current_state = external_sensor.get_current_instigator_state(stored_state)
    elif repository.has_external_schedule(selector.name):
        external_schedule = repository.get_external_schedule(selector.name)
        stored_state = graphene_info.context.instance.get_instigator_state(
            external_schedule.get_external_origin_id(),
            external_schedule.selector_id,
        )
        current_state = external_schedule.get_current_instigator_state(stored_state)
    else:
        return GrapheneInstigationStateNotFoundError(selector.name)

    return GrapheneInstigationState(current_state)


def get_tick_log_events(graphene_info: "ResolveInfo", tick) -> "GrapheneInstigationEventConnection":
    from ..schema.instigation import GrapheneInstigationEvent, GrapheneInstigationEventConnection
    from ..schema.logs.log_level import GrapheneLogLevel

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
