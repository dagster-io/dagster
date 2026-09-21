import os

import dagster as dg


# start_get_deployment_name
def get_deployment_name() -> str:
    """Return the current Dagster+ deployment name, falling back to 'local'."""
    return os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "local")


# end_get_deployment_name


# start_raw_assets
@dg.asset(group_name="raw_data", tags={"layer": "raw"})
def raw_orders(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Ingest raw orders from source system.

    In a real pipeline this would read from a database or API.
    The source connection varies by deployment environment.
    """
    deployment = get_deployment_name()
    source_db = os.getenv("SOURCE_DATABASE_URL", "sqlite:///local.db")
    context.log.info(f"Reading orders from {source_db} (deployment={deployment})")

    row_count = 1000 if deployment == "prod" else 100
    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(row_count),
            "deployment": dg.MetadataValue.text(deployment),
            "source": dg.MetadataValue.text(source_db),
        }
    )


@dg.asset(group_name="raw_data", tags={"layer": "raw"})
def raw_customers(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Ingest raw customers from source system."""
    deployment = get_deployment_name()
    context.log.info(f"Reading customers (deployment={deployment})")

    row_count = 5000 if deployment == "prod" else 50
    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(row_count),
            "deployment": dg.MetadataValue.text(deployment),
        }
    )


# end_raw_assets


# start_staging_assets
@dg.asset(group_name="staging", tags={"layer": "staging"}, deps=[raw_orders])
def cleaned_orders(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Clean and validate raw orders."""
    deployment = get_deployment_name()
    context.log.info(f"Cleaning orders (deployment={deployment})")
    return dg.MaterializeResult(metadata={"deployment": dg.MetadataValue.text(deployment)})


@dg.asset(group_name="staging", tags={"layer": "staging"}, deps=[raw_customers])
def cleaned_customers(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Clean and validate raw customers."""
    deployment = get_deployment_name()
    context.log.info(f"Cleaning customers (deployment={deployment})")
    return dg.MaterializeResult(metadata={"deployment": dg.MetadataValue.text(deployment)})


# end_staging_assets


# start_analytics_assets
@dg.asset(
    group_name="analytics",
    tags={"layer": "analytics", "domain": "revenue"},
    deps=[cleaned_orders, cleaned_customers],
)
def daily_revenue(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Compute daily revenue metrics by joining orders and customers."""
    deployment = get_deployment_name()
    warehouse = os.getenv("WAREHOUSE_URL", "duckdb:///local_warehouse.db")
    context.log.info(f"Computing revenue → {warehouse} (deployment={deployment})")
    return dg.MaterializeResult(
        metadata={
            "deployment": dg.MetadataValue.text(deployment),
            "warehouse": dg.MetadataValue.text(warehouse),
        }
    )


# end_analytics_assets
