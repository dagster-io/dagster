from dagster._core.libraries import DagsterLibraryRegistry

from .hooks import pagerduty_on_failure as pagerduty_on_failure
from .resources import (
    PagerDutyService as PagerDutyService,
    pagerduty_resource as pagerduty_resource,
)
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-pagerduty", __version__)
