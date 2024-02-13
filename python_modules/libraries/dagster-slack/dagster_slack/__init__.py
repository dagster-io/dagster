from dagster._core.libraries import DagsterLibraryRegistry

from .hooks import (
    slack_on_failure as slack_on_failure,
    slack_on_success as slack_on_success,
)
from .resources import (
    SlackResource as SlackResource,
    slack_resource as slack_resource,
)
from .sensors import (
    make_slack_on_freshness_policy_status_change_sensor as make_slack_on_freshness_policy_status_change_sensor,
    make_slack_on_run_failure_sensor as make_slack_on_run_failure_sensor,
)
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-slack", __version__)
