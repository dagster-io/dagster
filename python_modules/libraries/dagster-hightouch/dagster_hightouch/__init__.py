from dagster._core.libraries import DagsterLibraryRegistry

from dagster_hightouch.component import HightouchSyncComponent
from dagster_hightouch.ops import hightouch_sync_op
from dagster_hightouch.resources import HightouchResource
from dagster_hightouch.version import __version__

DagsterLibraryRegistry.register("dagster-hightouch", __version__)

__all__ = [
    "HightouchResource",
    "HightouchSyncComponent",
    "__version__",
    "hightouch_sync_op",
]
