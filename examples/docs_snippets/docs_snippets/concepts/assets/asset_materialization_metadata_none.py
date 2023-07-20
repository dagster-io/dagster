from dagster import AssetExecutionContext, asset


@asset
def table1(context: AssetExecutionContext) -> None:
    ...  # write out some data to table1
    context.add_output_metadata(metadata={"num_rows": 25})
