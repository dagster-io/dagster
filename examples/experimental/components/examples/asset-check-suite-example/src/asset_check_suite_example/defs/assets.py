import dagster as dg
import polars as pl


@dg.asset
def raw(): ...


@dg.asset
def prepared() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "user_id": [1, 2, 3, 4, 5],
            "username": ["alice", "bob", "charlie", "dave", "eve"],
            "age": [28, 35, 42, 25, 31],
            "city": ["New York", "San Francisco", "Chicago", "Boston", "Seattle"],
            "active": [True, False, True, True, False],
        }
    )


@dg.asset
def enriched(): ...
