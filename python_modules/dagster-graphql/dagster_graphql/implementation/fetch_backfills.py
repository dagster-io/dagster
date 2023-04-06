from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.execution.backfill import BulkActionStatus

from .utils import capture_error

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo

    from ..schema.backfill import (
        GraphenePartitionBackfill,
        GraphenePartitionBackfills,
    )


@capture_error
def get_backfill(graphene_info: "ResolveInfo", backfill_id: str) -> "GraphenePartitionBackfill":
    from ..schema.backfill import GraphenePartitionBackfill

    # get_backfill can return None but this resolver assumes that the backfill exists
    backfill_job = check.not_none(graphene_info.context.instance.get_backfill(backfill_id))
    return GraphenePartitionBackfill(backfill_job)


@capture_error
def get_backfills(
    graphene_info: "ResolveInfo",
    status: Optional[BulkActionStatus] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> "GraphenePartitionBackfills":
    from ..schema.backfill import GraphenePartitionBackfill, GraphenePartitionBackfills

    backfills = graphene_info.context.instance.get_backfills(
        status=status, cursor=cursor, limit=limit
    )
    return GraphenePartitionBackfills(
        results=[GraphenePartitionBackfill(backfill) for backfill in backfills]
    )
