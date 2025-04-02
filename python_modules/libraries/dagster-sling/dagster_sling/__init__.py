from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_sling.asset_decorator import sling_assets
from dagster_sling.components.sling_replication_collection.component import (
    SlingReplicationCollectionComponent,
)
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_sling.resources import SlingConnectionResource, SlingMode, SlingResource
from dagster_sling.sling_replication import SlingReplicationParam
from dagster_sling.version import __version__

__all__ = [
    "DagsterSlingTranslator",
    "SlingConnectionResource",
    "SlingMode",
    "SlingReplicationCollectionComponent",
    "SlingReplicationParam",
    "SlingResource",
    "sling_assets",
]

DagsterLibraryRegistry.register("dagster-sling", __version__)
