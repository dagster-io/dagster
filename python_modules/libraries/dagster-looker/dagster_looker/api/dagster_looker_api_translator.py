from typing import Dict

from dagster import (
    AssetSpec,
    _check as check,
)
from dagster._record import record
from looker_sdk.sdk.api40.models import LookmlModelExplore


@record
class LookerInstanceData:
    """A record representing all content in a Looker instance."""

    explores_by_id: Dict[str, LookmlModelExplore]


class DagsterLookerApiTranslator:
    def get_explore_asset_spec(self, lookml_explore: LookmlModelExplore) -> AssetSpec:
        return AssetSpec(
            key=check.not_none(lookml_explore.id),
            tags={
                "dagster/kind/looker": "",
                "dagster/kind/explore": "",
            },
        )

    def get_asset_spec(self, api_model: LookmlModelExplore) -> AssetSpec:
        return self.get_explore_asset_spec(api_model)
