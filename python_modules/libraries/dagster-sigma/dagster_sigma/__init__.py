from dagster._core.libraries import DagsterLibraryRegistry

from dagster_sigma.resource import (
    SigmaBaseUrl as SigmaBaseUrl,
    SigmaOrganization as SigmaOrganization,
)

# Move back to version.py and edit setup.py once we are ready to publish.
__version__ = "1!0+dev"

DagsterLibraryRegistry.register("dagster-sigma", __version__)
