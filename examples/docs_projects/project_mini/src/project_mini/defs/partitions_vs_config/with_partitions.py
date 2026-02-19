import dagster as dg

customer_partitions = dg.StaticPartitionsDefinition(["customer_a", "customer_b", "customer_c"])


@dg.asset(partitions_def=customer_partitions)
def customer_orders(context: dg.AssetExecutionContext):
    """Fetch and process orders for a specific customer partition."""
    customer_id = context.partition_key
    context.log.info(f"Fetching orders for customer: {customer_id}")

    orders = [
        {"order_id": f"{customer_id}-001", "amount": 150.00},
        {"order_id": f"{customer_id}-002", "amount": 275.50},
        {"order_id": f"{customer_id}-003", "amount": 89.99},
    ]

    context.log.info(f"Processed {len(orders)} orders for {customer_id}")
    return orders


@dg.asset(partitions_def=customer_partitions, deps=[customer_orders])
def customer_summary(context: dg.AssetExecutionContext):
    """Generate a summary report for a specific customer partition."""
    customer_id = context.partition_key
    context.log.info(f"Generating summary for customer: {customer_id}")

    summary = {
        "customer_id": customer_id,
        "total_orders": 3,
        "total_revenue": 515.49,
    }

    context.log.info(f"Summary for {customer_id}: {summary}")
    return summary


@dg.schedule(
    cron_schedule="0 1 * * *",
    job=dg.define_asset_job(
        "all_customers_job",
        selection=[customer_orders, customer_summary],
        partitions_def=customer_partitions,
    ),
)
def daily_customer_schedule():
    """Trigger processing for all customer partitions."""
    for partition_key in customer_partitions.get_partition_keys():
        yield dg.RunRequest(partition_key=partition_key)
