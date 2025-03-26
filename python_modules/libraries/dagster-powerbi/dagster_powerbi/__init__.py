from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_powerbi.assets import (
    build_semantic_model_refresh_asset_definition as build_semantic_model_refresh_asset_definition,
)
from dagster_powerbi.resource import (
    PowerBIServicePrincipal as PowerBIServicePrincipal,
    PowerBIToken as PowerBIToken,
    PowerBIWorkspace as PowerBIWorkspace,
    load_powerbi_asset_specs as load_powerbi_asset_specs,
)
from dagster_powerbi.translator import DagsterPowerBITranslator as DagsterPowerBITranslator
from dagster_powerbi.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-powerbi", __version__)
