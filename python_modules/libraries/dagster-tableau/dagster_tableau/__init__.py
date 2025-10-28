from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_tableau.asset_decorator import tableau_assets as tableau_assets
from dagster_tableau.asset_utils import (
    parse_tableau_external_and_materializable_asset_specs as parse_tableau_external_and_materializable_asset_specs,
)
from dagster_tableau.assets import (
    build_tableau_materializable_assets_definition as build_tableau_materializable_assets_definition,
)
from dagster_tableau.components import TableauComponent as TableauComponent
from dagster_tableau.resources import (
    TableauCloudWorkspace as TableauCloudWorkspace,
    TableauServerWorkspace as TableauServerWorkspace,
    load_tableau_asset_specs as load_tableau_asset_specs,
)
from dagster_tableau.translator import (
    DagsterTableauTranslator as DagsterTableauTranslator,
    TableauContentType as TableauContentType,
    TableauTranslatorData as TableauTranslatorData,
)
from dagster_tableau.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-tableau", __version__)
