from dagster import load_assets_from_package_module, repository, with_resources
from dagstermill import ConfigurableLocalOutputNotebookIOManager

from . import assets
from .jobs import ping_noteable


@repository
def finished_tutorial():
    return [
        with_resources(
            load_assets_from_package_module(assets),
            resource_defs={
                "output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager(),
            },
        ),
        ping_noteable,
    ]
