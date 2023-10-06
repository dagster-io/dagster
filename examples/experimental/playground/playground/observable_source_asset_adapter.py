from datetime import datetime

from dagster import Definitions, observable_source_asset
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.external_asset import create_external_asset_from_source_asset


@observable_source_asset
def always_return_time() -> DataVersion:
    return DataVersion(datetime.now().strftime("%H:%M:%S"))


defs = Definitions(assets=[create_external_asset_from_source_asset(always_return_time)])
