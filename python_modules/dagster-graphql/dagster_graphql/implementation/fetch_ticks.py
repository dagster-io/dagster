import warnings
from typing import TYPE_CHECKING, Optional, Sequence

import pendulum
from dagster._core.scheduler.instigation import (
    InstigatorType,
    TickStatus,
)

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo
    from .loader import RepositoryScopedBatchLoader


def get_instigation_ticks(
    graphene_info: "ResolveInfo",
    instigator_type: InstigatorType,
    instigator_origin_id: str,
    selector_id: str,
    batch_loader: Optional["RepositoryScopedBatchLoader"],
    dayRange: Optional[int],
    dayOffset: Optional[int],
    limit: Optional[int],
    cursor: Optional[str],
    status_strings: Optional[Sequence[str]],
):
    from ..schema.instigation import GrapheneInstigationTick

    before = None
    if dayOffset:
        before = pendulum.now("UTC").subtract(days=dayOffset).timestamp()
    elif cursor:
        parts = cursor.split(":")
        if parts:
            try:
                before = float(parts[-1])
            except (ValueError, IndexError):
                warnings.warn(f"Invalid cursor for ticks: {cursor}")

    after = (
        pendulum.now("UTC").subtract(days=dayRange + (dayOffset or 0)).timestamp()
        if dayRange
        else None
    )
    statuses = [TickStatus(status) for status in status_strings] if status_strings else None

    if batch_loader and limit and not cursor and not before and not after:
        if instigator_type == InstigatorType.SENSOR:
            ticks = batch_loader.get_sensor_ticks(
                instigator_origin_id,
                selector_id,
                limit,
            )
        elif instigator_type == InstigatorType.SCHEDULE:
            ticks = batch_loader.get_schedule_ticks(
                instigator_origin_id,
                selector_id,
                limit,
            )
        else:
            raise Exception(f"Unexpected instigator type {instigator_type}")

        return [GrapheneInstigationTick(graphene_info, tick) for tick in ticks]

    return [
        GrapheneInstigationTick(graphene_info, tick)
        for tick in graphene_info.context.instance.get_ticks(
            instigator_origin_id,
            selector_id,
            before=before,
            after=after,
            limit=limit,
            statuses=statuses,
        )
    ]
