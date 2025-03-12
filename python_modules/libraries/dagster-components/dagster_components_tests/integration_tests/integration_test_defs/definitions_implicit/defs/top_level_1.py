import dagster as dg


@dg.asset
def top_level_1() -> None:
    pass
