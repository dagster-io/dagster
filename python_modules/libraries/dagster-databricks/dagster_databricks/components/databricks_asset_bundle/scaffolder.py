import os

from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel, Field


class DatabricksAssetBundleScaffoldParams(BaseModel):
    """Parameters for scaffolding DatabricksAssetBundleComponent from Databricks asset bundle."""

    databricks_configs_path: str = Field(
        description="Path to the databricks.yml config file",
    )


class DatabricksAssetBundleScaffolder(Scaffolder[DatabricksAssetBundleScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[DatabricksAssetBundleScaffoldParams]:
        return DatabricksAssetBundleScaffoldParams

    def scaffold(self, request: ScaffoldRequest[DatabricksAssetBundleScaffoldParams]) -> None:
        project_root = request.project_root or os.getcwd()
        project_root_tmpl = "{{ project_root }}"
        rel_path = os.path.relpath(request.params.databricks_configs_path, start=project_root)
        path_str = f"{project_root_tmpl}/{rel_path}"

        scaffold_component(request, {"configs": path_str})
