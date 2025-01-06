from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from typing import Any, Optional, Union

from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    ConfigurableResource,
    MaterializeResult,
    MetadataValue,
    OpExecutionContext,
    TableColumnConstraints,
    _check as check,
)
from dagster._annotations import public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dlt.common.pipeline import LoadInfo
from dlt.common.schema import Schema
from dlt.extract.resource import DltResource
from dlt.extract.source import DltSource
from dlt.pipeline.pipeline import Pipeline

from dagster_dlt.constants import META_KEY_PIPELINE, META_KEY_SOURCE, META_KEY_TRANSLATOR
from dagster_dlt.dlt_event_iterator import DltEventIterator, DltEventType
from dagster_dlt.translator import DagsterDltTranslator, DltResourceTranslatorData


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
            from zoneinfo import ZoneInfo

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

    def _extract_table_schema_metadata(self, table_name: str, schema: Schema) -> TableSchema:
        # Pyright does not detect the default value from 'pop' and 'get'
        try:
            table_schema = TableSchema(
                columns=[
                    TableColumn(
                        name=column.pop("name", ""),  # type: ignore
                        type=column.pop("data_type", "string"),  # type: ignore
                        constraints=TableColumnConstraints(
                            nullable=column.pop("nullable", True),  # type: ignore
                            unique=column.pop("unique", False),  # type: ignore
                            other=[*column.keys()],  # e.g. "primary_key" or "foreign_key"
                        ),
                    )
                    for column in schema.get_table_columns(table_name).values()
                ]
            )
        except KeyError:
            # We want the asset to materialize even if we failed to extract the table schema.
            table_schema = TableSchema(columns=[])
        return table_schema

    def extract_resource_metadata(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        resource: DltResource,
        load_info: LoadInfo,
        dlt_pipeline: Pipeline,
    ) -> Mapping[str, Any]:
        """Helper method to extract dlt resource metadata from load info dict.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): Asset or op execution context
            resource (DltResource): The dlt resource being materialized
            load_info (LoadInfo): Run metadata from dlt `pipeline.run(...)`
            dlt_pipeline (Pipeline): The dlt pipeline used by `resource`

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
        default_schema = dlt_pipeline.default_schema
        normalized_table_name = default_schema.naming.normalize_table_identifier(
            str(resource.table_name)
        )
        # job metadata for specific target `normalized_table_name`
        base_metadata["jobs"] = [
            job
            for load_package in load_info_dict.get("load_packages", [])
            for job in load_package.get("jobs", [])
            if job.get("table_name") == normalized_table_name
        ]
        rows_loaded = dlt_pipeline.last_trace.last_normalize_info.row_counts.get(
            normalized_table_name
        )
        if rows_loaded:
            base_metadata["rows_loaded"] = MetadataValue.int(rows_loaded)

        schema: Optional[str] = None
        for load_package in load_info_dict.get("load_packages", []):
            for table in load_package.get("tables", []):
                if table.get("name") == normalized_table_name:
                    schema = table.get("schema_name")
                    break
            if schema:
                break

        destination_name: Optional[str] = base_metadata.get("destination_name")
        table_name = None
        if destination_name and schema:
            table_name = ".".join([destination_name, schema, normalized_table_name])

        child_table_names = [
            name
            for name in default_schema.data_table_names()
            if name.startswith(f"{normalized_table_name}__")
        ]
        child_table_schemas = {
            table_name: self._extract_table_schema_metadata(table_name, default_schema)
            for table_name in child_table_names
        }
        table_schema = self._extract_table_schema_metadata(normalized_table_name, default_schema)

        base_metadata = {
            **child_table_schemas,
            **base_metadata,
            **TableMetadataSet(
                column_schema=table_schema,
                table_name=table_name,
            ),
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
    ) -> DltEventIterator[DltEventType]:
        """Runs the dlt pipeline with subset support.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): Asset or op execution context
            dlt_source (Optional[DltSource]): optional dlt source if resource is used from an `@op`
            dlt_pipeline (Optional[Pipeline]): optional dlt pipeline if resource is used from an `@op`
            dagster_dlt_translator (Optional[DagsterDltTranslator]): optional dlt translator if resource is used from an `@op`
            **kwargs (dict[str, Any]): Keyword args passed to pipeline `run` method

        Returns:
            DltEventIterator[DltEventType]: An iterator of MaterializeResult or AssetMaterialization

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
        return DltEventIterator(
            self._run(
                context=context,
                dlt_source=dlt_source,
                dlt_pipeline=dlt_pipeline,
                dagster_dlt_translator=dagster_dlt_translator,
                **kwargs,
            ),
            context=context,
            dlt_pipeline=dlt_pipeline,
        )

    def _run(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        dlt_source: DltSource,
        dlt_pipeline: Pipeline,
        dagster_dlt_translator: DagsterDltTranslator,
        **kwargs,
    ) -> Iterator[DltEventType]:
        """Runs the dlt pipeline with subset support.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): Asset or op execution context
            dlt_source (Optional[DltSource]): optional dlt source if resource is used from an `@op`
            dlt_pipeline (Optional[Pipeline]): optional dlt pipeline if resource is used from an `@op`
            dagster_dlt_translator (Optional[DagsterDltTranslator]): optional dlt translator if resource is used from an `@op`
            **kwargs (dict[str, Any]): Keyword args passed to pipeline `run` method

        Returns:
            DltEventIterator[DltEventType]: An iterator of MaterializeResult or AssetMaterialization

        """
        asset_key_dlt_source_resource_mapping = {
            dagster_dlt_translator.get_asset_spec(
                DltResourceTranslatorData(
                    resource=dlt_source_resource, destination=dlt_pipeline.destination
                )
            ).key: dlt_source_resource
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

        for (
            asset_key,
            dlt_source_resource,
        ) in asset_key_dlt_source_resource_mapping.items():
            metadata = self.extract_resource_metadata(
                context, dlt_source_resource, load_info, dlt_pipeline
            )

            if has_asset_def:
                yield MaterializeResult(asset_key=asset_key, metadata=metadata)

            else:
                yield AssetMaterialization(asset_key=asset_key, metadata=metadata)
