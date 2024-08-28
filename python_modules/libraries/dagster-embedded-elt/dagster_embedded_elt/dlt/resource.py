from datetime import datetime, timezone
from typing import Any, Iterator, Mapping, Optional, Union

from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    ConfigurableResource,
    MaterializeResult,
    OpExecutionContext,
    _check as check,
)
from dagster._annotations import experimental, public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dlt.common.pipeline import LoadInfo
from dlt.extract.resource import DltResource
from dlt.extract.source import DltSource
from dlt.pipeline.pipeline import Pipeline

from dagster_embedded_elt.dlt.constants import (
    META_KEY_PIPELINE,
    META_KEY_SOURCE,
    META_KEY_TRANSLATOR,
)
from dagster_embedded_elt.dlt.translator import DagsterDltTranslator


@experimental
class DagsterDltResource(ConfigurableResource):
    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _cast_load_info_metadata(self, mapping: Mapping[Any, Any]) -> Mapping[Any, Any]:
        """Converts datetime and timezone values in a mapping to strings.

        Workaround for dagster._core.errors.DagsterInvalidMetadata: Could not resolve the metadata
        value for "jobs" to a known type. Value is not JSON serializable.

        Args:
            mapping (Mapping): Dictionary possibly containing datetime/timezone values

        Returns:
            Mapping[Any, Any]: Metadata with datetime and timezone values casted to strings

        """
        try:
            # zoneinfo is python >= 3.9
            from zoneinfo import ZoneInfo  # type: ignore

            casted_instance_types = (datetime, timezone, ZoneInfo)
        except:
            from dateutil.tz import tzfile

            casted_instance_types = (datetime, timezone, tzfile)

        def _recursive_cast(value: Any):
            if isinstance(value, dict):
                return {k: _recursive_cast(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_recursive_cast(item) for item in value]
            elif isinstance(value, casted_instance_types):
                return str(value)
            else:
                return value

        return {k: _recursive_cast(v) for k, v in mapping.items()}

    def extract_resource_metadata(
        self, resource: DltResource, load_info: LoadInfo
    ) -> Mapping[str, Any]:
        """Helper method to extract dlt resource metadata from load info dict.

        Args:
            resource (DltResource): The dlt resource being materialized
            load_info (LoadInfo): Run metadata from dlt `pipeline.run(...)`

        Returns:
            Mapping[str, Any]: Asset-specific metadata dictionary

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

        table_columns = [
            TableColumn(name=column.get("name"), type=column.get("data_type"))
            for pkg in load_info_dict.get("load_packages", [])
            for table in pkg.get("tables", [])
            for column in table.get("columns", [])
            if table.get("name") == resource.table_name
        ]
        base_metadata = {
            **base_metadata,
            **TableMetadataSet(column_schema=TableSchema(columns=table_columns)),
        }

        return base_metadata

    @public
    def run(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        dlt_source: Optional[DltSource] = None,
        dlt_pipeline: Optional[Pipeline] = None,
        dagster_dlt_translator: Optional[DagsterDltTranslator] = None,
        **kwargs,
    ) -> Iterator[Union[MaterializeResult, AssetMaterialization]]:
        """Runs the dlt pipeline with subset support.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): Asset or op execution context
            dlt_source (Optional[DltSource]): optional dlt source if resource is used from an `@op`
            dlt_pipeline (Optional[Pipeline]): optional dlt pipeline if resource is used from an `@op`
            dagster_dlt_translator (Optional[DagsterDltTranslator]): optional dlt translator if resource is used from an `@op`
            **kwargs (dict[str, Any]): Keyword args passed to pipeline `run` method

        Returns:
            Iterator[Union[MaterializeResult, AssetMaterialization]]: An iterator of MaterializeResult or AssetMaterialization

        """
        # This resource can be used in both `asset` and `op` definitions. In the context of an asset
        # execution, we retrieve the dlt source, pipeline, and translator from the asset metadata
        # as a fallback mechanism. We give preference to explicit parameters to make it easy to
        # customize execution, e.g., when using partitions.
        if isinstance(context, AssetExecutionContext):
            metadata_by_key = context.assets_def.metadata_by_key
            first_asset_metadata = next(iter(metadata_by_key.values()))

            dlt_source = check.inst(
                dlt_source or first_asset_metadata.get(META_KEY_SOURCE), DltSource
            )
            dlt_pipeline = check.inst(
                dlt_pipeline or first_asset_metadata.get(META_KEY_PIPELINE), Pipeline
            )
            dagster_dlt_translator = check.inst(
                dagster_dlt_translator or first_asset_metadata.get(META_KEY_TRANSLATOR),
                DagsterDltTranslator,
            )

        dlt_source = check.not_none(
            dlt_source, "dlt_source is a required parameter in an op context"
        )
        dlt_pipeline = check.not_none(
            dlt_pipeline, "dlt_pipeline is a required parameter in an op context"
        )

        # Default to base translator if undefined
        dagster_dlt_translator = dagster_dlt_translator or DagsterDltTranslator()

        asset_key_dlt_source_resource_mapping = {
            dagster_dlt_translator.get_asset_key(dlt_source_resource): dlt_source_resource
            for dlt_source_resource in dlt_source.selected_resources.values()
        }

        # Filter sources by asset key sub-selection
        if context.is_subset:
            asset_key_dlt_source_resource_mapping = {
                asset_key: asset_dlt_source_resource
                for (
                    asset_key,
                    asset_dlt_source_resource,
                ) in asset_key_dlt_source_resource_mapping.items()
                if asset_key in context.selected_asset_keys
            }
            dlt_source = dlt_source.with_resources(
                *[
                    dlt_source_resource.name
                    for dlt_source_resource in asset_key_dlt_source_resource_mapping.values()
                    if dlt_source_resource
                ]
            )

        load_info = dlt_pipeline.run(dlt_source, **kwargs)

        load_info.raise_on_failed_jobs()

        has_asset_def: bool = bool(context and context.has_assets_def)

        for asset_key, dlt_source_resource in asset_key_dlt_source_resource_mapping.items():
            metadata = self.extract_resource_metadata(dlt_source_resource, load_info)

            if has_asset_def:
                yield MaterializeResult(asset_key=asset_key, metadata=metadata)

            else:
                yield AssetMaterialization(asset_key=asset_key, metadata=metadata)
