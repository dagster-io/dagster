import os
from pathlib import Path
from typing import Literal, Optional

from dagster import AssetExecutionContext, Definitions, define_asset_job
from dagster_blueprints import YamlBlueprintsLoader
from dagster_blueprints.blueprint import Blueprint
from dagster_dbt import DbtCliResource, build_dbt_asset_selection, dbt_assets

dbt_project_dir = Path(__file__).parent.parent / "jaffle_shop"
dbt_manifest_path = dbt_project_dir / "target" / "manifest.json"


@dbt_assets(manifest=dbt_manifest_path)
def jaffle_shop_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


class DbtSelectJobBlueprint(Blueprint):
    type: Literal["dbt_select_job"]
    name: str
    select: str
    exclude: Optional[str]

    def build_defs(self) -> Definitions:
        job_def = define_asset_job(
            name=self.name,
            selection=build_dbt_asset_selection(
                [jaffle_shop_dbt_assets], dbt_select=self.select, dbt_exclude=self.exclude
            ),
        )
        return Definitions(jobs=[job_def])


loader = YamlBlueprintsLoader(
    per_file_blueprint_type=DbtSelectJobBlueprint,
    path=Path(__file__).parent / "dbt_jobs.yaml",
)
resources = {"dbt": DbtCliResource(project_dir=os.fspath(dbt_project_dir))}

defs = Definitions.merge(
    Definitions(assets=[jaffle_shop_dbt_assets], resources=resources),
    loader.load_defs(resources=resources),
)
