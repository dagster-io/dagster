from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_msteams.card import Card as Card
from dagster_msteams.hooks import (
    teams_on_failure as teams_on_failure,
    teams_on_success as teams_on_success,
)
from dagster_msteams.resources import (
    MSTeamsResource as MSTeamsResource,
    msteams_resource as msteams_resource,
)
from dagster_msteams.sensors import (
    make_teams_on_run_failure_sensor as make_teams_on_run_failure_sensor,
)
from dagster_msteams.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-msteams", __version__)
