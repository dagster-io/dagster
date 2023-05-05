from dagster._core.libraries import DagsterLibraryRegistry

from .card import Card as Card
from .hooks import (
    teams_on_failure as teams_on_failure,
    teams_on_success as teams_on_success,
)
from .resources import (
    MSTeamsResource as MSTeamsResource,
    msteams_resource as msteams_resource,
)
from .sensors import make_teams_on_run_failure_sensor as make_teams_on_run_failure_sensor
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-msteams", __version__)
