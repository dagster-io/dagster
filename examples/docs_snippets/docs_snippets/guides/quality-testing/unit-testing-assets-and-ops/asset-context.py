import dagster as dg


@dg.asset(partitions_def=dg.DailyPartitionsDefinition("2024-01-01"))
def loaded_file(context: dg.AssetExecutionContext) -> str:
    with open(f"path_{context.partition_key}.txt") as file:
        return file.read()


# highlight-start
def test_loaded_file() -> None:
    context = dg.build_asset_context(partition_key="2024-08-16")
    assert loaded_file(context) == "Contents for August 16th, 2024"
    # highlight-end
