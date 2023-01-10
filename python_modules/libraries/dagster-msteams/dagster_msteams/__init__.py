from dagster._core.utils import check_dagster_package_version

from .card import Card as Card
from .hooks import (
    teams_on_failure as teams_on_failure,
    teams_on_success as teams_on_success,
)
from .resources import msteams_resource as msteams_resource
from .sensors import make_teams_on_run_failure_sensor as make_teams_on_run_failure_sensor
from .version import __version__ as __version__

check_dagster_package_version("dagster-msteams", __version__)
