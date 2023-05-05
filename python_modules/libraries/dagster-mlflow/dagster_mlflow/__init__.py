from dagster._core.libraries import DagsterLibraryRegistry

from .hooks import end_mlflow_on_run_finished
from .resources import mlflow_tracking
from .version import __version__

DagsterLibraryRegistry.register("dagster-mlflow", __version__)

__all__ = ["mlflow_tracking", "end_mlflow_on_run_finished"]
