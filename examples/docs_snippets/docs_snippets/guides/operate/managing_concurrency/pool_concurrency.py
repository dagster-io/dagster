import time

import dagster as dg


@dg.asset(pool="database")
def query_customers(context: dg.AssetExecutionContext):
    """Asset assigned to the 'database' pool."""
    context.log.info("Querying customers table...")
    time.sleep(5)  # Simulate database query
    return {"count": 1000}


@dg.asset(pool="database")
def query_orders(context: dg.AssetExecutionContext):
    """Asset assigned to the 'database' pool."""
    context.log.info("Querying orders table...")
    time.sleep(5)  # Simulate database query
    return {"count": 5000}


@dg.asset(pool="api")
def fetch_external_data(context: dg.AssetExecutionContext):
    """Asset assigned to the 'api' pool."""
    context.log.info("Fetching from external API...")
    time.sleep(3)  # Simulate API call
    return {"status": "success"}
