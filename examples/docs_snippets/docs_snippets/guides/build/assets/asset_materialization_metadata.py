from pandas import DataFrame

from dagster import Output, asset


@asset
def table1() -> Output[DataFrame]:
    df = DataFrame({"col1": [1, 2], "col2": [3, 4]})
    return Output(df, metadata={"num_rows": df.shape[0]})
