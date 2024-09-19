from typing import TYPE_CHECKING, Optional

from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus

if TYPE_CHECKING:
    from dagster_graphql.schema.backfill import (
        GraphenePartitionBackfill,
        GraphenePartitionBackfills,
    )
    from dagster_graphql.schema.util import ResolveInfo


def get_backfill(graphene_info: "ResolveInfo", backfill_id: str) -> "GraphenePartitionBackfill":
    from dagster_graphql.schema.backfill import (
        GrapheneBackfillNotFoundError,
        GraphenePartitionBackfill,
    )

    backfill_job = graphene_info.context.instance.get_backfill(backfill_id)
    if backfill_job is None:
        return GrapheneBackfillNotFoundError(backfill_id)

    return GraphenePartitionBackfill(backfill_job)


def get_backfills(
    graphene_info: "ResolveInfo",
    filters: Optional[BulkActionsFilter] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    status: Optional[BulkActionStatus] = None,
) -> "GraphenePartitionBackfills":
    from dagster_graphql.schema.backfill import (
        GraphenePartitionBackfill,
        GraphenePartitionBackfills,
    )

    backfills = graphene_info.context.instance.get_backfills(
        status=status, cursor=cursor, limit=limit, filters=filters
    )
    return GraphenePartitionBackfills(
        results=[GraphenePartitionBackfill(backfill) for backfill in backfills]
    )
