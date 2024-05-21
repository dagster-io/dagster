from typing import Dict, Mapping, Sequence, Tuple, Union, cast

from pydantic import BaseModel

from dagster._annotations import experimental
from dagster._core.instance import DagsterInstance

from ..asset_check_spec import AssetCheckKey, AssetCheckSeverity, AssetCheckSpec
from ..asset_checks import AssetChecksDefinition
from ..asset_key import AssetKey, CoercibleToAssetKey
from ..assets import AssetsDefinition, SourceAsset
from ..events import AssetMaterialization
from ..metadata import TableColumn, TableMetadataSet, TableSchema
from .utils import build_multi_asset_check


@experimental
def build_column_schema_change_checks(
    *,
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    severity: AssetCheckSeverity = AssetCheckSeverity.WARN,
) -> Sequence[AssetChecksDefinition]:
    """Returns asset checks that pass if the column schema of the asset's latest materialization
    is the same as the column schema of the asset's previous materialization.

    Args:
        assets (Sequence[Union[AssetKey, str, AssetsDefinition, SourceAsset]]): The assets to create
            asset checks for.
        severity (AssetCheckSeverity): The severity if the check fails. Defaults to WARN.

    Returns:
        Sequence[AssetsChecksDefinition]
    """
    asset_keys = set()
    for el in assets:
        if isinstance(el, AssetsDefinition):
            asset_keys |= el.keys
        elif isinstance(el, SourceAsset):
            asset_keys.add(el.key)
        else:
            asset_keys.add(AssetKey.from_coercible(el))

    def _result_for_check_key(
        instance: DagsterInstance, asset_check_key: AssetCheckKey
    ) -> Tuple[bool, str]:
        materialization_records = instance.fetch_materializations(
            limit=2, records_filter=asset_check_key.asset_key
        ).records
        if len(materialization_records) < 2:
            return True, "The asset has been materialized fewer than 2 times"

        record, prev_record = materialization_records
        metadata = cast(AssetMaterialization, record.asset_materialization).metadata
        prev_metadata = cast(AssetMaterialization, prev_record.asset_materialization).metadata

        column_schema = TableMetadataSet.extract(metadata).column_schema
        prev_column_schema = TableMetadataSet.extract(prev_metadata).column_schema
        if column_schema is None:
            return False, "Latest materialization has no column schema metadata"
        if prev_column_schema is None:
            return False, "Previous materialization has no column schema metadata"

        diff = TableSchemaDiff.from_table_schemas(prev_column_schema, column_schema)
        if diff.added_columns or diff.removed_columns or diff.column_type_changes:
            description = "Column schema changed between previous and latest materialization."
            if diff.added_columns:
                description += (
                    f"\n\nAdded columns: {', '.join(col.name for col in diff.added_columns)}"
                )

            if diff.removed_columns:
                description += (
                    f"\n\nRemoved columns: {', '.join(col.name for col in diff.removed_columns)}"
                )

            if diff.column_type_changes:
                description += "\n\nColumn type changes:"
                for col_name, type_change in diff.column_type_changes.items():
                    description += (
                        f"\n- {col_name}: {type_change.old_type} -> {type_change.new_type}"
                    )

            return False, description

        return True, "No changes to column schema between previous and latest materialization"

    return build_multi_asset_check(
        check_specs=[
            AssetCheckSpec(
                "column_schema_change",
                asset=asset_key,
                description="Checks whether there are changes to column schema between the asset's "
                " two most recent materializations",
            )
            for asset_key in asset_keys
        ],
        check_fn=_result_for_check_key,
        severity=severity,
    )


class TypeChange(BaseModel):
    old_type: str
    new_type: str


class TableSchemaDiff(BaseModel):
    added_columns: Sequence[TableColumn]
    removed_columns: Sequence[TableColumn]
    column_type_changes: Mapping[str, TypeChange]

    @staticmethod
    def from_table_schemas(
        old_table_schema: TableSchema, new_table_schema: TableSchema
    ) -> "TableSchemaDiff":
        old_columns_by_key = {column.name: column for column in old_table_schema.columns}
        new_columns_by_key = {column.name: column for column in new_table_schema.columns}

        added_columns = [
            column for column in new_table_schema.columns if column.name not in old_columns_by_key
        ]
        removed_columns = [
            column for column in old_table_schema.columns if column.name not in new_columns_by_key
        ]
        column_type_changes: Dict[str, TypeChange] = {}
        for name, new_column in new_columns_by_key.items():
            old_column = old_columns_by_key.get(name)
            if old_column is not None and old_column.type != new_column.type:
                column_type_changes[name] = TypeChange(
                    old_type=old_column.type, new_type=new_column.type
                )

        return TableSchemaDiff(
            added_columns=added_columns,
            removed_columns=removed_columns,
            column_type_changes=column_type_changes,
        )
