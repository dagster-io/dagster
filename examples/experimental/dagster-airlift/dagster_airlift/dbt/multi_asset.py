import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dagster import AssetExecutionContext, Definitions
from dagster_dbt import DbtCliResource, dbt_assets

from dagster_airlift.core import DefsFactory


@dataclass
class DbtProjectDefs(DefsFactory):
    dbt_project_path: Path
    name: str
    group: Optional[str] = None

    def build_defs(self) -> Definitions:
        dbt_manifest_path = self.dbt_project_path / "target" / "manifest.json"

        @dbt_assets(manifest=json.loads(dbt_manifest_path.read_text()), name=self.name)
        def _dbt_asset(context: AssetExecutionContext, dbt: DbtCliResource):
            yield from dbt.cli(["build"], context=context).stream()

        if self.group:
            _dbt_asset = _dbt_asset.with_attributes(
                group_names_by_key={key: self.group for key in _dbt_asset.keys}
            )

        return Definitions(
            assets=[_dbt_asset],
            resources={
                "dbt": DbtCliResource(
                    project_dir=self.dbt_project_path, profiles_dir=self.dbt_project_path
                )
            },
        )
