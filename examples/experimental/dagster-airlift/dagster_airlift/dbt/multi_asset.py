import json
import os
from pathlib import Path
from typing import Literal, Optional

from dagster import AssetExecutionContext, Definitions
from dagster_blueprints.blueprint import Blueprint
from dagster_dbt import DbtCliResource, dbt_assets
from pydantic import BaseModel


class FromEnvVar(BaseModel):
    env_var: str


class DbtProjectDefs(Blueprint):
    type: Literal["dbt_project"] = "dbt_project"
    dbt_project_path: FromEnvVar
    group: Optional[str] = None

    def build_defs(self) -> Definitions:
        source_file_name_without_ext = self.source_file_name.split(".")[0]
        dbt_project_path = Path(os.environ[self.dbt_project_path.env_var])
        dbt_manifest_path = dbt_project_path / "target" / "manifest.json"

        @dbt_assets(
            manifest=json.loads(dbt_manifest_path.read_text()),
            name=source_file_name_without_ext,
        )
        def _dbt_asset(context: AssetExecutionContext, dbt: DbtCliResource):
            yield from dbt.cli(["build"], context=context).stream()

        if self.group:
            _dbt_asset = _dbt_asset.with_attributes(
                group_names_by_key={key: self.group for key in _dbt_asset.keys}
            )
        return Definitions(
            assets=[_dbt_asset],
            resources={
                "dbt": DbtCliResource(project_dir=dbt_project_path, profiles_dir=dbt_project_path)
            },
        )
