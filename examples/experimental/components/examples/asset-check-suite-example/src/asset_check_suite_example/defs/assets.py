import dagster as dg
import polars as pl


@dg.asset(kinds={"polars"}, description="Raw users data")
def users_raw():
    return pl.DataFrame(
        {
            "user_id": [1, 2, 3, 4, 5],
            "username": ["alice", "bob", "charlie", "dave", "eve"],
            "age": [28, 35, 42, 25, 31],
            "city": ["New York", "San Francisco", "Chicago", "Boston", "Seattle"],
            "active": [True, False, True, True, False],
        }
    )


@dg.asset(kinds={"polars"}, description="Prepared users data")
def users_prepared(users_raw) -> pl.DataFrame:
    return users_raw


@dg.asset(kinds={"polars"}, description="Enriched users data")
def users_summary(users_prepared):
    return users_prepared.select(
        [
            pl.col("age").mean().alias("avg_age"),
            pl.col("age").min().alias("min_age"),
            pl.col("age").max().alias("max_age"),
            pl.col("active").sum().alias("active_users"),
            pl.col("user_id").count().alias("total_users"),
        ]
    )
