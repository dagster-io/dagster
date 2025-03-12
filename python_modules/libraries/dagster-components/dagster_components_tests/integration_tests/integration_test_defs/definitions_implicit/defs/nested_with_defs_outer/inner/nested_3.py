import dagster as dg


@dg.asset
def nested_3() -> None: ...


@dg.asset
def not_included() -> None: ...
