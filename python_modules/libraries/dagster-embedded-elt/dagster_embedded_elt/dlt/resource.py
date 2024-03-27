from typing import TYPE_CHECKING, Any, Iterator, Mapping, Union

from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    ConfigurableResource,
    MaterializeResult,
    OpExecutionContext,
)
from dagster._annotations import public
from dlt.common.pipeline import LoadInfo
from dlt.extract.resource import DltResource

if TYPE_CHECKING:
    from dlt.extract.source import DltSource
    from dlt.pipeline.pipeline import Pipeline

from .constants import META_KEY_PIPELINE, META_KEY_SOURCE


class DltDagsterResource(ConfigurableResource):
    def _cast_load_info_metadata(self, mapping: Mapping[Any, Any]) -> Mapping[Any, Any]:
        """Converts pendulum DateTime and Timezone values in a mapping to strings.

        Workaround for dagster._core.errors.DagsterInvalidMetadata: Could not resolve the
        metadata value for "jobs" to a known type. Value is not JSON serializable.

        Args:
            mapping (Mapping): dictionary possibly containing pendulum values

        Returns:
            mapping with pendulum DateTime and Timezone values casted to strings

        """
        from pendulum import DateTime, Timezone  # type: ignore

        def _recursive_cast(value: Any):
            if isinstance(value, dict):
                return {k: _recursive_cast(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_recursive_cast(item) for item in value]
            elif isinstance(value, (DateTime, Timezone)):
                return str(value)
            else:
                return value

        return {k: _recursive_cast(v) for k, v in mapping.items()}

    def extract_resource_metadata(
        self, resource: DltResource, load_info: LoadInfo
    ) -> Mapping[str, Any]:
        """Helper method to extract dlt resource metadata from load info dict.

        Args:
            resource (DltResource) dlt resource being materialized
            load_info (LoadInfo) run metadata from dlt pipeline.run(...)

        Returns:
            Mapping[str, Any]: asset-specific metadata dictionary

        """
        dlt_base_metadata_types = {
            "first_run",
            "started_at",
            "finished_at",
            "dataset_name",
            "destination_name",
            "destination_type",
        }

        load_info_dict = self._cast_load_info_metadata(load_info.asdict())

        # shared metadata that is displayed for all assets
        base_metadata = {k: v for k, v in load_info_dict.items() if k in dlt_base_metadata_types}

        # job metadata for specific target `resource.table_name`
        base_metadata["jobs"] = [
            job
            for load_package in load_info_dict.get("load_packages", [])
            for job in load_package.get("jobs", [])
            if job.get("table_name") == resource.table_name
        ]

        return base_metadata

    @public
    def run(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        **kwargs,
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        """Runs dlt pipeline.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]) execution context
            **kwargs (dict[str, Any]) keyword args passed to pipeline `run` method

        Returns:
            Iterator[Union[AssetMaterialization, MaterializeResult]] materialization in asset or op

        """
        metadata_by_key = context.assets_def.metadata_by_key
        first_asset_metadata = next(iter(metadata_by_key.values()))

        dlt_source: DltSource | None = first_asset_metadata.get(META_KEY_SOURCE)
        dlt_pipeline: Pipeline | None = first_asset_metadata.get(META_KEY_PIPELINE)

        if not dlt_source or not dlt_pipeline:
            raise Exception(
                "%s and %s must be defined on AssetSpec metadata",
                META_KEY_SOURCE,
                META_KEY_PIPELINE,
            )

        # Mapping of asset keys to dlt resources
        asset_key_dlt_source_resource_mapping = zip(
            context.selected_asset_keys, dlt_source.resources.values()
        )

        # Filter sources by asset key sub-selection
        if context.is_subset:
            asset_key_dlt_source_resource_mapping = [
                (asset_key, dlt_source_resource)
                for (asset_key, dlt_source_resource) in asset_key_dlt_source_resource_mapping
                if asset_key in context.selected_asset_keys
            ]
            dlt_source = dlt_source.with_resources(
                *[
                    dlt_source_resource.name
                    for (_, dlt_source_resource) in asset_key_dlt_source_resource_mapping
                ]
            )

        load_info = dlt_pipeline.run(dlt_source, **kwargs)

        for asset_key, dlt_source_resource in asset_key_dlt_source_resource_mapping:
            metadata = self.extract_resource_metadata(dlt_source_resource, load_info)
            if isinstance(context, AssetExecutionContext):
                yield MaterializeResult(asset_key=asset_key, metadata=metadata)

            else:
                yield AssetMaterialization(asset_key=asset_key, metadata=metadata)
