import dagster as dg

adhoc_request_job = dg.define_asset_job(
    name="adhoc_request_job",
    selection=dg.AssetSelection.assets("adhoc_request"),
)
