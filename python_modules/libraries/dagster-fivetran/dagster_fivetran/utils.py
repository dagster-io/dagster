from typing import Any, Dict, Iterator, List, Optional

from dagster_fivetran.types import FivetranOutput

import dagster._check as check
from dagster import AssetMaterialization, MetadataValue


def get_fivetran_connector_url(connector_details: Dict[str, Any]) -> str:
    service = connector_details["service"]
    schema = connector_details["schema"]
    return f"https://fivetran.com/dashboard/connectors/{service}/{schema}"


def get_fivetran_logs_url(connector_details: Dict[str, Any]) -> str:
    return f"{get_fivetran_connector_url(connector_details)}/logs"


def _table_data_to_materialization(
    fivetran_output: FivetranOutput,
    asset_key_prefix: List[str],
    schema_name: str,
    table_data: Dict[str, Any],
) -> Optional[AssetMaterialization]:
    table_name = table_data["name_in_destination"]
    asset_key = asset_key_prefix + [schema_name, table_name]
    if not table_data["enabled"]:
        return None
    metadata: Dict[str, MetadataValue] = {
        "connector_url": MetadataValue.url(
            get_fivetran_connector_url(fivetran_output.connector_details)
        )
    }
    if table_data.get("columns"):
        metadata["column_info"] = MetadataValue.json(check.dict_elem(table_data, "columns"))
    return AssetMaterialization(
        asset_key=asset_key,
        description=f"Table generated via Fivetran sync: {schema_name}.{table_name}",
        metadata=metadata,
    )


def generate_materializations(
    fivetran_output: FivetranOutput, asset_key_prefix: List[str]
) -> Iterator[AssetMaterialization]:
    for schema in fivetran_output.schema_config["schemas"].values():
        schema_name = schema["name_in_destination"]
        schema_prefix = fivetran_output.connector_details.get("config", {}).get("schema_prefix")
        if schema_prefix:
            schema_name = f"{schema_prefix}_{schema_name}"
        if not schema["enabled"]:
            continue
        for table_data in schema["tables"].values():
            mat = _table_data_to_materialization(
                fivetran_output, asset_key_prefix, schema_name, table_data
            )
            if mat is not None:
                yield mat
