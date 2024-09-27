
import dagster as dg

adhoc_request = dg.AssetSelection.keys("adhoc_request")

adhoc_request_job = dg.define_asset_job(
    name="adhoc_request_job",
    selection=adhoc_request
)

analysis_assets = dg.AssetSelection.keys("joined_data").upstream() 

analysis_update_job = dg.define_asset_job(
    name="analysis_update_job",
    selection=analysis_assets,
)