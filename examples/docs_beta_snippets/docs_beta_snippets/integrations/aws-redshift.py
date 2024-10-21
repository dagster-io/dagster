from dagster_aws.redshift import RedshiftClientResource

import dagster as dg


@dg.asset
def example_redshift_asset(context, redshift: RedshiftClientResource):
    result = redshift.get_client().execute_query("SELECT 1", fetch_results=True)
    context.log.info(f"Query result: {result}")


redshift_configured = RedshiftClientResource(
    host="my-redshift-cluster.us-east-1.redshift.amazonaws.com",
    port=5439,
    user="dagster",
    password=dg.EnvVar("DAGSTER_REDSHIFT_PASSWORD"),
    database="dev",
)

defs = dg.Definitions(
    assets=[example_redshift_asset],
    resources={"redshift": redshift_configured},
)
