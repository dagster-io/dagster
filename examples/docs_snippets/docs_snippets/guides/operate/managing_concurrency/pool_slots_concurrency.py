import time

import dagster as dg


@dg.asset(pool="database", pool_slots=3)
def build_reporting_table(context: dg.AssetExecutionContext):
    """Heavy asset that occupies 3 slots of the 'database' pool while executing."""
    context.log.info("Running expensive aggregation query...")
    time.sleep(10)  # Simulate a heavy database workload
    return {"rows": 10_000_000}


@dg.asset(pool="database")
def query_customers(context: dg.AssetExecutionContext):
    """Light asset that occupies 1 slot (the default) of the 'database' pool."""
    context.log.info("Querying customers table...")
    time.sleep(5)  # Simulate database query
    return {"count": 1000}


@dg.op(pool="database", pool_slots=2)
def sync_warehouse(context: dg.OpExecutionContext):
    """Op that occupies 2 slots of the 'database' pool while executing."""
    context.log.info("Syncing warehouse tables...")
    time.sleep(5)  # Simulate a moderately heavy database workload
