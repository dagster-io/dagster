from dagstermill import local_output_notebook_io_manager
from tutorial_notebook_assets import assets
from tutorial_notebook_assets.jobs import ping_noteable

from dagster import load_assets_from_package_module, repository, with_resources


@repository
def tutorial_notebook_assets():
    return [
        with_resources(
            load_assets_from_package_module(assets),
            resource_defs={
                "output_notebook_io_manager": local_output_notebook_io_manager,
            },
        ),
        ping_noteable,
    ]
