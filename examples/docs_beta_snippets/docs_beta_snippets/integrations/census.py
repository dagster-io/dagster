from dagster_census import CensusResource

import dagster as dg


@dg.asset
def census_source(census: CensusResource):
    census.get_source(source_id=1)


defs = dg.Definitions(
    assets=[census_source],
    resources={"census": CensusResource(api_key=dg.EnvVar("CENSUS_API_KEY"))},
)
