# pyright: reportMissingImports=none

# start
# __init__.py

from my_dagster_project import assets
from my_dagster_project.resources import github_api

from dagster import Definitions, load_assets_from_package_module

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        "github_api": github_api.configured(
            {"access_token": {"env": "GITHUB_ACCESS_TOKEN"}}
        )
    },
)


# end
