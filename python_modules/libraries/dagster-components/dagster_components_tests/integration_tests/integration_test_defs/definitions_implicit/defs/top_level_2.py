import dagster as dg

from .top_level_1 import top_level_1  # noqa


@dg.asset
def top_level_2() -> None:
    pass


@dg.asset
def not_in_defs() -> None:
    pass


defs = dg.Definitions(assets=[top_level_1, top_level_2])
