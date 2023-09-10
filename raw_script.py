
from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset, materialize


@asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-03"))
def a_partitioned_asset(context: AssetExecutionContext):
    assert context.asset_partition_key_for_output("result") == "2020-01-01"

    # expected = (
    #     "AssetExecutionContext.asset_partition_key_for_output is deprecated and will be removed"
    #     " in 1.7. You have called method asset_partition_key_for_output on"
    #     " AssetExecutionContext that is oriented around I/O managers. If you not using I/O"
    #     " managers we suggest you use partition_key_range instead. If you are using I/O"
    #     " managers the method still exists at"
    #     " op_execution_context.asset_partition_key_for_output."
    # )

    # assert expected in str(exc_info.value)

    # called["yup"] = True

materialize(assets=[a_partitioned_asset], partition_key="2020-01-01")