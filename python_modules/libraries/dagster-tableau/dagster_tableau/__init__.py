from dagster._core.libraries import DagsterLibraryRegistry

from dagster_tableau.resources import (
    TableauCloudWorkspace as TableauCloudWorkspace,
    TableauServerWorkspace as TableauServerWorkspace,
)
from dagster_tableau.translator import DagsterTableauTranslator as DagsterTableauTranslator

# Move back to version.py and edit setup.py once we are ready to publish.
__version__ = "0.0.2"

DagsterLibraryRegistry.register("dagster-tableau", __version__)
