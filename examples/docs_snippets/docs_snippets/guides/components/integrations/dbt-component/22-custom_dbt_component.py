import json
from collections.abc import Iterator, Mapping
from datetime import timedelta
from typing import Any, Optional

from dagster_dbt import DbtCliResource, DbtProject, DbtProjectComponent

import dagster as dg


class CustomDbtProjectComponent(DbtProjectComponent):
    """Custom DbtProjectComponent with op config and metadata customization."""

    @property
    def op_config_schema(self) -> type[dg.Config]:
        class CustomDbtConfig(dg.Config):
            full_refresh: bool = False

        return CustomDbtConfig

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Optional[DbtProject]
    ) -> dg.AssetSpec:
        base_spec = super().get_asset_spec(manifest, unique_id, project)
        dbt_props = self.get_resource_props(manifest, unique_id)

        # Add a custom metadata field with the model name
        return base_spec.merge_attributes(
            metadata={
                "dbt_model_name": dbt_props["name"],
            }
        )

    def execute(
        self, context: dg.AssetExecutionContext, dbt: DbtCliResource
    ) -> Iterator:
        dbt_vars = {
            # custom time range that includes 3 hours of lookback to ensure we don't miss any data
            "min_date": (
                context.partition_time_window.start - timedelta(hours=3)
            ).isoformat(),
            "max_date": context.partition_time_window.end.isoformat(),
        }
        # Build CLI args based on config
        args = (
            ["build", "--full-refresh"]
            if context.op_config.get("full_refresh", False)
            else ["build", "--vars", json.dumps(dbt_vars)]
        )
        yield from dbt.cli(args, context=context).stream()
