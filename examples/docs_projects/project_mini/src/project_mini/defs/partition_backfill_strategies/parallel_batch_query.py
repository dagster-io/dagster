import dagster as dg

customer_partitions = dg.StaticPartitionsDefinition(
    ["customer_a", "customer_b", "customer_c", "customer_d", "customer_e"]
)


@dg.asset(
    partitions_def=customer_partitions,
    backfill_policy=dg.BackfillPolicy.multi_run(max_partitions_per_run=10),
)
def process_customers_batch(context: dg.AssetExecutionContext) -> None:
    """Process all partitions in a single database query."""
    customer_ids = context.partition_keys

    # Single query for all customers - most efficient for databases
    query = "SELECT * FROM customers WHERE customer_id IN %s"
    results = execute_query(query, customer_ids)

    context.log.info(f"Processed {len(results)} customers in single query")


def execute_query(query: str, params: list) -> list:
    # Simulated database query
    return [{"customer_id": p, "data": "..."} for p in params]
