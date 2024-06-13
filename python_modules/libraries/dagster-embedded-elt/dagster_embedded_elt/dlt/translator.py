from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from dagster import AssetKey, AutoMaterializePolicy
from dagster._annotations import public
from dlt.extract.resource import DltResource


@dataclass
class DagsterDltTranslator:
    @public
    def get_asset_key(self, resource: DltResource) -> AssetKey:
        """Defines asset key for a given dlt resource key and dataset name.

        Args:
            resource (DltResource): dlt resource / transformer

        Returns:
            AssetKey of Dagster asset derived from dlt resource

        """
        return AssetKey(f"dlt_{resource.source_name}_{resource.name}")

    @public
    def get_deps_asset_keys(self, resource: DltResource) -> Iterable[AssetKey]:
        """Defines upstream asset dependencies given a dlt resource.

        Defaults to a concatenation of `resource.source_name` and `resource.name`.

        Args:
            resource (DltResource): dlt resource / transformer

        Returns:
            Iterable[AssetKey]: The Dagster asset keys upstream of `dlt_resource_key`.

        """
        return [AssetKey(f"{resource.source_name}_{resource.name}")]

    @public
    def get_auto_materialize_policy(self, resource: DltResource) -> Optional[AutoMaterializePolicy]:
        """Defines resource specific auto materialize policy.

        Args:
            resource (DltResource): dlt resource / transformer

        Returns:
            Optional[AutoMaterializePolicy]: The automaterialize policy for a resource

        """
        return None

    @public
    def get_metadata(self, resource: DltResource) -> Mapping[str, Any]:
        """Defines resource specific metadata.

        Args:
            resource (DltResource): dlt resource / transformer

        Returns:
            Mapping[str, Any]: The custom metadata entries for this resource.
        """
        return {}
