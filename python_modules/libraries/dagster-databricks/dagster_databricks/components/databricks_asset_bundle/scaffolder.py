from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel


class DatabricksAssetBundleScaffoldParams(BaseModel):
    pass


class DatabricksAssetBundleScaffolder(Scaffolder[DatabricksAssetBundleScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[DatabricksAssetBundleScaffoldParams]:
        return DatabricksAssetBundleScaffoldParams

    def scaffold(self, request: ScaffoldRequest[DatabricksAssetBundleScaffoldParams]) -> None:
        raise NotImplementedError()
