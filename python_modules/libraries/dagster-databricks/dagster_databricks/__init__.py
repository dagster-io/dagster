"""Databricks integration for Dagster.

This package provides:

- the :py:class:`~dagster_databricks.databricks_pyspark_step_launcher` resource, which
    launches a Databricks job in which an op can be run
- the :py:class:`~dagster_databricks.DatabricksRunJobSolidDefinition`, which can be used
    to execute an arbitrary task in Databricks.
"""

from dagster._core.libraries import DagsterLibraryRegistry

from .databricks import DatabricksClient, DatabricksError, DatabricksJobRunner
from .databricks_pyspark_step_launcher import (
    DatabricksConfig,
    DatabricksPySparkStepLauncher,
    databricks_pyspark_step_launcher,
)
from .ops import (
    create_databricks_run_now_op,
    create_databricks_submit_run_op,
)
from .resources import databricks_client
from .version import __version__

DagsterLibraryRegistry.register("dagster-databricks", __version__)

__all__ = [
    "create_databricks_run_now_op",
    "create_databricks_submit_run_op",
    "databricks_client",
    "DatabricksClient",
    "DatabricksConfig",
    "DatabricksError",
    "DatabricksJobRunner",
    "DatabricksPySparkStepLauncher",
    "databricks_pyspark_step_launcher",
]
