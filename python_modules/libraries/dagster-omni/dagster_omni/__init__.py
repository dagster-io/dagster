from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_omni.resources import (
    OmniWorkspace as OmniWorkspace,
    load_omni_asset_specs as load_omni_asset_specs,
)
from dagster_omni.translator import (
    DagsterOmniTranslator as DagsterOmniTranslator,
    OmniContentData as OmniContentData,
    OmniContentType as OmniContentType,
    OmniTranslatorData as OmniTranslatorData,
    OmniWorkspaceData as OmniWorkspaceData,
)
from dagster_omni.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-omni", __version__)
