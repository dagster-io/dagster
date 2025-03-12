import dagster as dg


@dg.asset
def dont_include() -> None: ...
