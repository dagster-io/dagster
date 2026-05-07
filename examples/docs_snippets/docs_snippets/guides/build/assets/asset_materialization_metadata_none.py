from dagster import Output, asset


@asset
def table1() -> Output[None]:
    ...  # write out some data to table1
    return Output(None, metadata={"num_rows": 25})
