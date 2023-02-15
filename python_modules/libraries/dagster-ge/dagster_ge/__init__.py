from dagster._core.libraries import DagsterLibraryRegistry

from .factory import ge_validation_op_factory
from .version import __version__

DagsterLibraryRegistry.register("dagster-ge", __version__)

__all__ = ["ge_validation_op_factory"]
