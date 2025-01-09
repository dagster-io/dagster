import warnings
from collections.abc import Sequence
from datetime import timedelta
from typing import TYPE_CHECKING, Optional

from dagster._core.scheduler.instigation import InstigatorType, TickStatus
from dagster._time import get_current_datetime

if TYPE_CHECKING:
    from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader
    from dagster_graphql.schema.util import ResolveInfo


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
    before: Optional[float],
    after: Optional[float],
):
    from dagster_graphql.schema.instigation import GrapheneInstigationTick

    if before is None:
        if dayOffset:
            before = (get_current_datetime() - timedelta(days=dayOffset)).timestamp()
        elif cursor:
            parts = cursor.split(":")
            if parts:
                try:
                    before = float(parts[-1])
                except (ValueError, IndexError):
                    warnings.warn(f"Invalid cursor for ticks: {cursor}")

    if after is None:
        after = (
            (get_current_datetime() - timedelta(days=dayRange + (dayOffset or 0))).timestamp()
            if dayRange
            else None
        )

    statuses = [TickStatus(status) for status in status_strings] if status_strings else None

    if batch_loader and limit and not cursor and not before and not after and not statuses:
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
    else:
        ticks = graphene_info.context.instance.get_ticks(
            instigator_origin_id,
            selector_id,
            before=before,
            after=after,
            limit=limit,
            statuses=statuses,
        )

    return [GrapheneInstigationTick(tick) for tick in ticks]
