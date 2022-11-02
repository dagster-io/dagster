from assets_notebook_template import assets
from assets_notebook_template.jobs import ping_noteable

from dagster import load_assets_from_package_module, repository


@repository
def assets_notebook_template():
    return [load_assets_from_package_module(assets), ping_noteable]
