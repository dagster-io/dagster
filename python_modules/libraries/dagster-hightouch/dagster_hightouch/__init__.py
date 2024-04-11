from dagster._core.libraries import DagsterLibraryRegistry

from .ops import (
    hightouch_sync_op as hightouch_sync_op,
)
from .resources import (
    HightouchResource as HightouchResource,
)
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-fivetran", __version__)
