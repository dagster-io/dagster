import os
import warnings
from collections.abc import Sequence
from datetime import timedelta
from typing import TYPE_CHECKING, Optional

from dagster._core.scheduler.instigation import InstigatorTick, InstigatorType, TickStatus
from dagster._time import get_current_datetime

from dagster_graphql.implementation.utils import get_query_limit_with_default

if TYPE_CHECKING:
    from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader
    from dagster_graphql.schema.util import ResolveInfo

MAX_TICKS_QUERY_LIMIT = int(os.getenv("DAGSTER_MAX_TICKS_QUERY_LIMIT", "1000"))


def get_instigation_ticks(
    graphene_info: "ResolveInfo",
    instigator_type: InstigatorType,
    instigator_origin_id: str,
    selector_id: str,
    batch_loader: Optional["RepositoryScopedBatchLoader"],
    dayRange: int | None,
    dayOffset: int | None,
    limit: int | None,
    cursor: str | None,
    status_strings: Sequence[str] | None,
    before: float | None,
    after: float | None,
):
    from dagster_graphql.schema.instigation import GrapheneInstigationTick

    limit = get_query_limit_with_default(limit, MAX_TICKS_QUERY_LIMIT)

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
        summaries = graphene_info.context.instance.get_tick_summaries(
            instigator_origin_id,
            selector_id,
            before=before,
            after=after,
            limit=limit,
            statuses=statuses,
        )
        # add tick ids to the prepare queue so that if a resolver fetches a tick_body, all tick_bodies are
        # loaded from the DB in a single batch
        InstigatorTick.prepare(graphene_info.context, [s.tick_id for s in summaries])
        return [GrapheneInstigationTick(summary) for summary in summaries]

    return [GrapheneInstigationTick(tick) for tick in ticks]
