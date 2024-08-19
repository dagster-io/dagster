from typing import Any, Literal, Mapping, Optional

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
from jinja2 import Template

from dagster_blueprints.blueprint import Blueprint


class DbtProjectBlueprint(Blueprint):
    """A blueprint that produces assets and checks from a dbt project."""

    type: Literal["dagster_dbt/project"]
    project_dir: str
    target_path: Optional[str] = "target"
    target: Optional[str] = None
    op_name: Optional[str] = None
    asset_key_template: Optional[str]

    def build_defs(self) -> Definitions:
        project = DbtProject(
            project_dir=self.project_dir, target_path=self.target_path, target=self.target
        )
        project.prepare_if_dev()

        @dbt_assets(
            name=self.op_name,
            dagster_dbt_translator=_build_translator(asset_key_template=self.asset_key_template),
        )
        def _dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
            yield from dbt.cli(["build"], context=context).stream()

        return Definitions(
            assets=[_dbt_assets], resources={"dbt": DbtCliResource(project_dir=project)}
        )


def _build_translator(asset_key_template: Optional[str]) -> DagsterDbtTranslator:
    if asset_key_template is None:
        return DagsterDbtTranslator()

    class CustomTranslator(DagsterDbtTranslator):
        def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
            template = Template(asset_key_template)
            return AssetKey.from_user_string(
                template.render(
                    name=dbt_resource_props.get("name"),
                    source_name=dbt_resource_props.get("source_name"),
                    resource_type=dbt_resource_props["resource_type"],
                    schema=dbt_resource_props["config"].get("schema"),
                    alias=dbt_resource_props["alias"],
                    version=dbt_resource_props["version"],
                )
            )
