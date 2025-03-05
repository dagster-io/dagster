from dagster import Definitions

from .side_asset import side_asset  # noqa for relative import

defs = Definitions(
    assets=[side_asset],
)
