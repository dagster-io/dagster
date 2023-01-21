from dagster import load_assets_from_package_module, repository, with_resources
from dagstermill import local_output_notebook_io_manager

from . import assets
from .jobs import ping_noteable


@repository
def template_tutorial():
    return [
        with_resources(
            load_assets_from_package_module(assets),
            resource_defs={
                "output_notebook_io_manager": local_output_notebook_io_manager,
            },
        ),
        ping_noteable,
    ]
