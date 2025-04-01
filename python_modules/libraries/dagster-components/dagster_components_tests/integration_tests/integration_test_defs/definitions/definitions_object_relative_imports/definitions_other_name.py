from dagster import Definitions, asset

from .other_file import asset_in_other_file  # noqa: TID252
from .some_file import asset_in_some_file  # noqa: TID252


@asset
def an_asset_that_is_not_included() -> None: ...


defs = Definitions(assets=[asset_in_some_file, asset_in_other_file])
