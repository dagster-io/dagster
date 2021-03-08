from dagster import Partition, PartitionSetDefinition


# start_def
def get_date_partitions():
    """Every day in the month of May, 2020"""
    return [Partition(f"2020-05-{str(day).zfill(2)}") for day in range(1, 32)]


def run_config_for_date_partition(partition):
    date = partition.value
    return {"solids": {"process_data_for_date": {"config": {"date": date}}}}


date_partition_set = PartitionSetDefinition(
    name="date_partition_set",
    pipeline_name="my_data_pipeline",
    partition_fn=get_date_partitions,
    run_config_fn_for_partition=run_config_for_date_partition,
)
# end_def
