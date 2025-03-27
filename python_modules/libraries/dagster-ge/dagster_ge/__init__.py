from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_ge.factory import ge_validation_op_factory
from dagster_ge.version import __version__

DagsterLibraryRegistry.register("dagster-ge", __version__)

__all__ = ["ge_validation_op_factory"]
