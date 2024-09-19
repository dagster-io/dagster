from dagster._core.libraries import DagsterLibraryRegistry

from dagster_sigma.resource import (
    SigmaBaseUrl as SigmaBaseUrl,
    SigmaOrganization as SigmaOrganization,
)
from dagster_sigma.translator import (
    DagsterSigmaTranslator as DagsterSigmaTranslator,
    SigmaDataset as SigmaDataset,
    SigmaWorkbook as SigmaWorkbook,
)

# Move back to version.py and edit setup.py once we are ready to publish.
__version__ = "0.0.10"

DagsterLibraryRegistry.register("dagster-sigma", __version__)
