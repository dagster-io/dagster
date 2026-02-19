from concurrent.futures import ProcessPoolExecutor

import dagster as dg

customer_partitions = dg.StaticPartitionsDefinition(
    ["customer_a", "customer_b", "customer_c", "customer_d", "customer_e"]
)


def analyze_one(customer_id: str) -> dict:
    """CPU-intensive analysis - must be defined at module level for ProcessPool."""
    # Simulated CPU-intensive work
    result = sum(i * i for i in range(100000))
    return {"customer_id": customer_id, "analysis": result}


@dg.asset(
    partitions_def=customer_partitions,
    backfill_policy=dg.BackfillPolicy.multi_run(max_partitions_per_run=10),
)
def analyze_customer_data(context: dg.AssetExecutionContext) -> None:
    """Use processes for parallel CPU-intensive work."""
    customer_ids = context.partition_keys

    # Use multiple CPU cores
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(analyze_one, customer_ids))

    context.log.info(f"Analyzed {len(results)} customers with process pool")
