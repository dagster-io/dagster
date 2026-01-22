from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_hightouch.component import HightouchSyncComponent
from dagster_hightouch.ops import hightouch_sync_op
from dagster_hightouch.resources import ConfigurableHightouchResource, HightouchResource
from dagster_hightouch.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-hightouch", __version__, is_dagster_package=True)

__all__ = [
    "ConfigurableHightouchResource",
    "HightouchResource",
    "HightouchSyncComponent",
    "hightouch_sync_op",
]
