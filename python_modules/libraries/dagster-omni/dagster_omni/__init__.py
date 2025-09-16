from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_omni.component import OmniComponent as OmniComponent
from dagster_omni.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-omni", __version__)
