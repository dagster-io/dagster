from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_polytomic.component import PolytomicComponent as PolytomicComponent
from dagster_polytomic.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-polytomic", __version__)
