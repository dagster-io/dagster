import dagster as dg


@dg.asset
def in_loose_defs() -> None: ...
