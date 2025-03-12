import dagster as dg


@dg.asset
def nested_2() -> None:
    pass


@dg.asset
def not_in_defs() -> None:
    pass


defs = dg.Definitions(assets=[nested_2])
