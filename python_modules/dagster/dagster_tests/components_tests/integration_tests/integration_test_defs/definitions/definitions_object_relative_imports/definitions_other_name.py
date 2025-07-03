import dagster as dg

from .other_file import asset_in_other_file  # noqa: TID252
from .some_file import asset_in_some_file  # noqa: TID252


@dg.asset
def an_asset_that_is_not_included() -> None: ...


defs = dg.Definitions(assets=[asset_in_some_file, asset_in_other_file])
