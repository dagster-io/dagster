from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_dlt.asset_decorator import build_dlt_asset_specs, dlt_assets
from dagster_dlt.components.dlt_load_collection.component import DltLoadCollectionComponent
from dagster_dlt.resource import DagsterDltResource
from dagster_dlt.translator import DagsterDltTranslator
from dagster_dlt.version import __version__

__all__ = [
    "DagsterDltResource",
    "DagsterDltTranslator",
    "DltLoadCollectionComponent",
    "build_dlt_asset_specs",
    "dlt_assets",
]


DagsterLibraryRegistry.register("dagster-dlt", __version__)
