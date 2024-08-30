from dagster._core.libraries import DagsterLibraryRegistry

from dagster_powerbi.resource import PowerBIWorkspace as PowerBIWorkspace
from dagster_powerbi.translator import DagsterPowerBITranslator as DagsterPowerBITranslator
from dagster_powerbi.version import __version__

DagsterLibraryRegistry.register("dagster-powerbi", __version__)
