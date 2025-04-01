import dagster as dg


@dg.asset
def defs_obj_inner() -> None: ...


@dg.asset
def not_included() -> None: ...
