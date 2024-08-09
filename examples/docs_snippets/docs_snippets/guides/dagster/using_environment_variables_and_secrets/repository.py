# pyright: reportMissingImports=none

# start
# definitions.py

from my_dagster_project import assets
from my_dagster_project.resources import GithubClientResource

from dagster import Definitions, EnvVar, load_assets_from_package_module

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        "github_api": GithubClientResource(access_token=EnvVar("GITHUB_ACCESS_TOKEN"))
    },
)


# end
