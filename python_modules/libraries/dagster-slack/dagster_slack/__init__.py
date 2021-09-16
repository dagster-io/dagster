from dagster.core.utils import check_dagster_package_version

from .hooks import slack_on_failure, slack_on_success
from .resources import slack_resource
from .sensors import make_slack_on_pipeline_failure_sensor, make_slack_on_run_failure_sensor
from .version import __version__

check_dagster_package_version("dagster-slack", __version__)

__all__ = ["slack_resource"]
