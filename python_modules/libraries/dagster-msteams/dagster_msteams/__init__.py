from dagster.core.utils import check_dagster_package_version

from .hooks import teams_on_failure, teams_on_success
from .resources import msteams_resource
from .card import Card
from .version import __version__

check_dagster_package_version("dagster-msteams", __version__)

__all__ = ["msteams_resource"]
