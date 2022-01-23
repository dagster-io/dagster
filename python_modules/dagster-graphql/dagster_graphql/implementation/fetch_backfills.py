from .utils import capture_error


@capture_error
def get_backfill(graphene_info, backfill_id):
    from ..schema.backfill import GraphenePartitionBackfill

    backfill_job = graphene_info.context.instance.get_backfill(backfill_id)
    return GraphenePartitionBackfill(backfill_job)


@capture_error
def get_backfills(graphene_info, status=None, cursor=None, limit=None):
    from ..schema.backfill import GraphenePartitionBackfill, GraphenePartitionBackfills

    backfills = graphene_info.context.instance.get_backfills(
        status=status, cursor=cursor, limit=limit
    )
    return GraphenePartitionBackfills(
        results=[GraphenePartitionBackfill(backfill) for backfill in backfills]
    )
