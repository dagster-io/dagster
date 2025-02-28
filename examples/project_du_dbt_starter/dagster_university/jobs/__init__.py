import dagster as dg

from ..partitions import monthly_partition, weekly_partition

trips_by_week = dg.AssetSelection.assets("trips_by_week")
adhoc_request = dg.AssetSelection.assets("adhoc_request")

trip_update_job = dg.define_asset_job(
    name="trip_update_job",
    partitions_def=monthly_partition,
    selection=dg.AssetSelection.all() - trips_by_week - adhoc_request,
)

weekly_update_job = dg.define_asset_job(
    name="weekly_update_job", partitions_def=weekly_partition, selection=trips_by_week
)

adhoc_request_job = dg.define_asset_job(name="adhoc_request_job", selection=adhoc_request)
