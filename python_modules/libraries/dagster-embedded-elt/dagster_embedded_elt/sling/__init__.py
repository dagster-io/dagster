from dagster._utils.warnings import deprecation_warning
from dagster_sling.asset_decorator import sling_assets
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_sling.resources import SlingConnectionResource, SlingMode, SlingResource
from dagster_sling.sling_replication import SlingReplicationParam

deprecation_warning(
    "The `dagster-embedded-elt` library",
    "0.26",
    additional_warn_text="Use `dagster-sling` instead.",
)

__all__ = [
    "DagsterSlingTranslator",
    "SlingConnectionResource",
    "SlingMode",
    "SlingReplicationParam",
    "SlingResource",
    "sling_assets",
]
