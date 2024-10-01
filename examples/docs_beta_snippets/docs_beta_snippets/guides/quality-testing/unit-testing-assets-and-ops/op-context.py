import dagster as dg


@dg.op
def load_file(context: dg.OpExecutionContext) -> str:
    with open(f"path_{context.partition_key}.txt") as file:
        return file.read()


# highlight-start
def test_load_file() -> None:
    context = dg.build_asset_context(partition_key="2024-08-16")
    assert load_file(context) == "Contents for August 16th, 2024"
    # highlight-end
