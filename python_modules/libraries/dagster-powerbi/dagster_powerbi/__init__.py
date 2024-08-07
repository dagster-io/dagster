from dagster._core.libraries import DagsterLibraryRegistry

from .resource import PowerBIWorkspace as PowerBIWorkspace
from .translator import DagsterPowerBITranslator as DagsterPowerBITranslator
from .version import __version__

DagsterLibraryRegistry.register("dagster-powerbi", __version__)
