from dagster_aws.athena import AthenaClientResource

import dagster as dg


@dg.asset
def example_athena_asset(athena: AthenaClientResource):
    return athena.get_client().execute_query("SELECT 1", fetch_results=True)


defs = dg.Definitions(
    assets=[example_athena_asset], resources={"athena": AthenaClientResource()}
)
