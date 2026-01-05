"""dbt assets with tests as asset checks.

dbt tests are automatically converted to Dagster asset checks,
covering:
- unique: Uniqueness dimension
- not_null: Completeness dimension
- relationships: Integrity dimension
- accepted_values: Consistency/Validity dimension
"""

from collections.abc import Mapping
from typing import Any, Optional

import dagster as dg
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    dbt_assets,
)

from data_quality_patterns.project import dbt_project

# Mapping from dbt source tables to Dagster asset keys
SOURCE_TO_ASSET_KEY = {
    ("raw", "customers"): dg.AssetKey("raw_customers"),
    ("raw", "orders"): dg.AssetKey("raw_orders"),
    ("raw", "products"): dg.AssetKey("raw_products"),
}


class DataQualityDbtTranslator(DagsterDbtTranslator):
    """Custom translator for dbt assets with asset checks enabled.

    Maps dbt sources to the corresponding raw Dagster assets so that
    the dbt models correctly depend on the raw data assets.
    """

    def __init__(self):
        super().__init__(
            settings=DagsterDbtTranslatorSettings(
                enable_asset_checks=True,  # Enable dbt tests as asset checks
            )
        )

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> dg.AssetKey:
        """Map dbt resources to Dagster asset keys.

        - Sources are mapped to raw_* asset keys
        - Models get a 'dbt' prefix
        """
        resource_type = dbt_resource_props.get("resource_type")

        if resource_type == "source":
            # Map dbt sources to raw Dagster assets
            source_name = dbt_resource_props.get("source_name")
            table_name = dbt_resource_props.get("name")

            source_key = (source_name, table_name)
            if source_key in SOURCE_TO_ASSET_KEY:
                return SOURCE_TO_ASSET_KEY[source_key]

            # Fallback: use source_table naming
            return dg.AssetKey(f"{source_name}_{table_name}")

        elif resource_type == "model":
            # Add 'dbt' prefix for models
            asset_key = super().get_asset_key(dbt_resource_props)
            return asset_key.with_prefix(["dbt"])

        return super().get_asset_key(dbt_resource_props)

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        """Assign dbt assets to groups based on their path."""
        resource_type = dbt_resource_props.get("resource_type")

        # Don't assign group to sources (they have their own group)
        if resource_type == "source":
            return None

        fqn = dbt_resource_props.get("fqn", [])

        if "staging" in fqn:
            return "dbt_staging"
        elif "marts" in fqn:
            return "dbt_marts"

        return "dbt"


@dbt_assets(
    manifest=dbt_project.manifest_path,
    project=dbt_project,
    dagster_dbt_translator=DataQualityDbtTranslator(),
)
def dbt_quality_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    """Build dbt models with tests as asset checks.

    The dbt tests defined in schema.yml files are automatically
    converted to Dagster asset checks:

    Staging tests:
    - stg_customers.customer_id: unique, not_null
    - stg_customers.email: not_null
    - stg_orders.order_id: unique, not_null
    - stg_orders.customer_id: not_null, relationships
    - stg_orders.amount: not_null

    Marts tests:
    - cleaned_customers.customer_id: unique, not_null
    - cleaned_customers.region: accepted_values
    - order_summary.customer_id: unique, not_null, relationships
    """
    yield from dbt.cli(["build"], context=context).stream()
