from dagster import AssetExecutionContext, asset


@asset
def my_asset(context: AssetExecutionContext) -> None:
    for i in range(10):
        print(f"Printing without context {i}")  # noqa: T201
        context.log.info(f"Logging using context {i}")
    try:
        raise Exception("This is an exception")
    except:
        return
