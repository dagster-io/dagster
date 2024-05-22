from dagster._core.libraries import DagsterLibraryRegistry

from .asset_decorator import looker_assets as looker_assets
from .dagster_looker_translator import (
    DagsterLookerTranslator as DagsterLookerTranslator,
    LookMLStructureType as LookMLStructureType,
)
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-looker", __version__)
