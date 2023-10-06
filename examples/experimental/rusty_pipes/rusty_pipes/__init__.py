import os
from tempfile import gettempdir

import polars as pl
from dagster import (
    AssetCheckResult,
    Definitions,
    PipesSubprocessClient,
    asset,
    asset_check,
)

RUST_DIR = os.path.join(os.path.dirname(__file__), "rust")


@asset
def some_dataframe() -> str:
    path = os.path.join(gettempdir(), "some_dataframe.csv")
    df = pl.DataFrame(
        {
            "value": [0, None, 2, 3],
        },
    )
    df.write_csv(path)
    return path


@asset_check(asset=some_dataframe)
def python_null_check(df_path: str):
    df = pl.read_csv(df_path)
    count = df.null_count()["value"][0]
    return AssetCheckResult(
        passed=(count == 0),
        metadata={
            "null_count": count,
        },
    )


@asset_check(asset=some_dataframe)
def rust_null_check(context, df_path: str) -> AssetCheckResult:
    pipes_client = PipesSubprocessClient()
    return pipes_client.run(
        context=context,
        command=["cargo", "run"],
        cwd=RUST_DIR,
        extras={"path": df_path},
        env=os.environ,
    ).get_asset_check_result()


defs = Definitions(
    assets=[some_dataframe],
    asset_checks=[
        python_null_check,
        rust_null_check,
    ],
)

if __name__ == "__main__":
    defs.get_implicit_global_asset_job_def().execute_in_process()
