from dagster import Definitions, load_assets_from_package_module
from dagstermill import ConfigurableLocalOutputNotebookIOManager

from . import assets

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={"output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager()},
)
