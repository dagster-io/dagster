from typing import Any
from dagster_dbt import dbt_assets, DbtCliResource
from dagster import Definitions
class LazyDbtProject:
    @classmethod
    def from_git_sha(cls, sha: str) -> "LazyDbtProject":
        pass

    def get_manifest(self) -> Any:
        pass
dbt_proj = LazyDbtProject.from_git_sha("https://my.git.sha")


@dbt_assets(manifest=dbt_proj.get_manifest())
def my_assets(): 
    pass

Definitions(assets=[my_assets], resources=DbtCliResource(manifest=dbt_proj.get_manifest(), project=dbt_proj))


