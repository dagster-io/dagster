from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_pagerduty.hooks import pagerduty_on_failure as pagerduty_on_failure
from dagster_pagerduty.resources import (
    PagerDutyService as PagerDutyService,
    pagerduty_resource as pagerduty_resource,
)
from dagster_pagerduty.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-pagerduty", __version__)
