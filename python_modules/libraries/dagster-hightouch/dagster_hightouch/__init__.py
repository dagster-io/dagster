from dagster_shared.libraries import DagsterLibraryRegistry
from .resources import ConfigurableHightouchResource, HightouchResource
from .ops import hightouch_sync_op
from .component import HightouchSyncComponent

from dagster_hightouch.version import __version__ as __version__

DagsterLibraryRegistry.register(
    "dagster-hightouch", __version__, is_dagster_package=True
)

__all__ = [
    "ConfigurableHightouchResource",
    "HightouchResource",
    "hightouch_sync_op",
    "HightouchSyncComponent",
]
