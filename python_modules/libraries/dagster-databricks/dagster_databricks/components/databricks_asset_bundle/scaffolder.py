import os

from dagster._annotations import preview
from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel, Field


@preview
class DatabricksAssetBundleScaffoldParams(BaseModel):
    """Parameters for scaffolding DatabricksAssetBundleComponent from Databricks asset bundle."""

    databricks_config_path: str = Field(
        description="Path to the databricks.yml config file",
    )
    databricks_workspace_host: str = Field(
        description="The host of your Databricks workspace.",
    )
    databricks_workspace_token: str = Field(
        description="The token to access your Databricks workspace.",
    )


@preview
class DatabricksAssetBundleScaffolder(Scaffolder[DatabricksAssetBundleScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[DatabricksAssetBundleScaffoldParams]:
        return DatabricksAssetBundleScaffoldParams

    def scaffold(self, request: ScaffoldRequest[DatabricksAssetBundleScaffoldParams]) -> None:
        project_root = request.project_root or os.getcwd()
        project_root_tmpl = "{{ project_root }}"

        rel_databricks_config_path = os.path.relpath(
            request.params.databricks_config_path, start=project_root
        )
        databricks_config_path_str = f"{project_root_tmpl}/{rel_databricks_config_path}"

        scaffold_component(
            request,
            {
                "databricks_config_path": databricks_config_path_str,
                "workspace": {
                    "host": request.params.databricks_workspace_host,
                    "token": request.params.databricks_workspace_token,
                },
            },
        )
