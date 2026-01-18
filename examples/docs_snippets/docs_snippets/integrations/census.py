from dagster_census import CensusResource

import dagster as dg


@dg.asset
def census_sync(census: CensusResource):
    census.trigger_sync_and_poll(sync_id=12345)


defs = dg.Definitions(
    assets=[census_sync],
    resources={"census": CensusResource(api_key=dg.EnvVar("CENSUS_API_KEY"))},
)
