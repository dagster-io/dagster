from concurrent.futures import ThreadPoolExecutor

import dagster as dg

customer_partitions = dg.StaticPartitionsDefinition(
    ["customer_a", "customer_b", "customer_c", "customer_d", "customer_e"]
)


@dg.asset(
    partitions_def=customer_partitions,
    backfill_policy=dg.BackfillPolicy.multi_run(max_partitions_per_run=10),
)
def fetch_customer_data(context: dg.AssetExecutionContext) -> None:
    """Use threads for parallel I/O operations."""
    customer_ids = context.partition_keys

    def fetch_one(customer_id):
        # Simulated API call
        return {"customer_id": customer_id, "data": f"data for {customer_id}"}

    # Process up to 5 customers concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_one, customer_ids))

    context.log.info(f"Fetched {len(results)} customers with thread pool")
