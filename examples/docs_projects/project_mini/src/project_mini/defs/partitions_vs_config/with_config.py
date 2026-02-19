import dagster as dg


class CustomerConfig(dg.Config):
    customer_id: str


@dg.asset
def customer_orders(context: dg.AssetExecutionContext, config: CustomerConfig):
    """Fetch and process orders for a specific customer."""
    customer_id = config.customer_id
    context.log.info(f"Fetching orders for customer: {customer_id}")

    orders = [
        {"order_id": f"{customer_id}-001", "amount": 150.00},
        {"order_id": f"{customer_id}-002", "amount": 275.50},
        {"order_id": f"{customer_id}-003", "amount": 89.99},
    ]

    context.log.info(f"Processed {len(orders)} orders for {customer_id}")
    return orders


@dg.asset(deps=[customer_orders])
def customer_summary(context: dg.AssetExecutionContext, config: CustomerConfig):
    """Generate a summary report for a specific customer."""
    customer_id = config.customer_id
    context.log.info(f"Generating summary for customer: {customer_id}")

    summary = {
        "customer_id": customer_id,
        "total_orders": 3,
        "total_revenue": 515.49,
    }

    context.log.info(f"Summary for {customer_id}: {summary}")
    return summary
