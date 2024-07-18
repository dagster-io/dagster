from dagster._core.libraries import DagsterLibraryRegistry

from .resource import SdfCliResource as SdfCliResource
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-sdf", __version__)
