from dagster._core.utils import check_dagster_package_version

from .card import Card
from .hooks import teams_on_failure, teams_on_success
from .resources import msteams_resource
from .sensors import make_teams_on_run_failure_sensor
from .version import __version__

check_dagster_package_version("dagster-msteams", __version__)

__all__ = ["msteams_resource"]
