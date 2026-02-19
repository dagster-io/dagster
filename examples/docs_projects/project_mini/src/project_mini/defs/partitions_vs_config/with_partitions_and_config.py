import dagster as dg

customer_partitions = dg.StaticPartitionsDefinition(["customer_a", "customer_b", "customer_c"])


class ProcessingConfig(dg.Config):
    include_archived: bool = False
    limit: int = 1000


@dg.asset(partitions_def=customer_partitions)
def customer_data(context: dg.AssetExecutionContext, config: ProcessingConfig):
    customer_id = context.partition_key
    context.log.info(f"Processing {customer_id} with include_archived={config.include_archived}")
