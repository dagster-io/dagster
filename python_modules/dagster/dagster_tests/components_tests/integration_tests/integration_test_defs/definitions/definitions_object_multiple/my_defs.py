from dagster import Definitions, asset


@asset
def a() -> None: ...


@asset
def b() -> None: ...


defs1 = Definitions(assets=[a])
defs2 = Definitions(assets=[b])
