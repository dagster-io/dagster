from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__ as __version__
from .asset_decorator import looker_assets as looker_assets
from .dagster_looker_translator import (
    LookMLStructureType as LookMLStructureType,
    DagsterLookerTranslator as DagsterLookerTranslator,
)

DagsterLibraryRegistry.register("dagster-looker", __version__)
