# start
# repository.py

from my_dagster_project import assets
from my_dagster_project.resources import github_api

from dagster import load_assets_from_package_module, repository, with_resources


@repository
def my_dagster_project():
    return [
        with_resources(
            load_assets_from_package_module(assets),
            {
                "github_api": github_api.configured(
                    {"access_token": {"env": "GITHUB_ACCESS_TOKEN"}}
                )
            },
        ),
    ]


# end
