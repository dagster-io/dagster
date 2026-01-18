from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_slack.hooks import (
    slack_on_failure as slack_on_failure,
    slack_on_success as slack_on_success,
)
from dagster_slack.resources import (
    SlackResource as SlackResource,
    slack_resource as slack_resource,
)
from dagster_slack.sensors import (
    make_slack_on_run_failure_sensor as make_slack_on_run_failure_sensor,
)
from dagster_slack.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-slack", __version__)
