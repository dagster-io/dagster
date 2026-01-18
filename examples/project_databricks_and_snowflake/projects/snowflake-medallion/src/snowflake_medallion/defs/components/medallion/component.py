from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

from dagster import AssetSpec, Component, Definitions, Model, Resolvable
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

from ...resources import SnowflakeResource, create_dbt_resource


class SnowflakeKindTranslator(DagsterDbtTranslator):
    """Custom translator that always shows Snowflake as the kind, even in demo mode."""

    def get_asset_spec(
        self,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional[Any],
    ) -> AssetSpec:
        spec = super().get_asset_spec(manifest, unique_id, project)
        return spec.replace_attributes(kinds={"snowflake", "dbt"})


class MedallionComponentParams(Model):
    demo_mode: bool = False
    account: str = ""
    user: str = ""
    password: str = ""
    warehouse: str = ""
    database: str = ""
    schema_name: str = "PUBLIC"


class MedallionComponent(Component, MedallionComponentParams, Resolvable):
    def build_defs(self, context) -> Definitions:
        snowflake = SnowflakeResource(
            account=self.account,
            user=self.user,
            password=self.password,
            warehouse=self.warehouse,
            database=self.database,
            db_schema=self.schema_name,
            demo_mode=self.demo_mode,
        )

        dbt = create_dbt_resource(demo_mode=self.demo_mode)

        project_dir = Path(__file__).parent.parent.parent.parent / "dbt_project"
        manifest_path = project_dir / "target" / "manifest.json"

        if not manifest_path.exists():
            return Definitions(
                assets=[],
                resources={
                    "snowflake": snowflake,
                    "dbt": dbt,
                },
            )

        @dbt_assets(
            manifest=manifest_path, dagster_dbt_translator=SnowflakeKindTranslator()
        )
        def medallion_dbt_assets(context, dbt: DbtCliResource):
            yield from dbt.cli(["build"], context=context).stream()

        return Definitions(
            assets=[medallion_dbt_assets],
            resources={
                "snowflake": snowflake,
                "dbt": dbt,
            },
        )
