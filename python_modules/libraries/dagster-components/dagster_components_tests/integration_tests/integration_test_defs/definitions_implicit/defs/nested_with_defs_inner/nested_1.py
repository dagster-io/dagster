import dagster as dg


@dg.asset
def nested_1() -> None:
    pass
