from tutorial_notebook_assets import assets
from tutorial_notebook_assets.jobs import ping_noteable

from dagster import load_assets_from_package_module, repository


@repository
def tutorial_notebook_assets():
    return [load_assets_from_package_module(assets), ping_noteable]
