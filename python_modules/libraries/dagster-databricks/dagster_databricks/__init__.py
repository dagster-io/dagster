"""Databricks integration for Dagster.

This package provides:

- the :py:class:`~dagster_databricks.databricks_pyspark_step_launcher` resource, which
    launches a Databricks job in which a solid can be run
- the :py:class:`~dagster_databricks.DatabricksRunJobSolidDefinition`, which can be used
    to execute an arbitrary task in Databricks.
"""

from dagster.core.utils import check_dagster_package_version

from .databricks import DatabricksError, DatabricksJobRunner
from .databricks_pyspark_step_launcher import (
    DatabricksConfig,
    DatabricksPySparkStepLauncher,
    databricks_pyspark_step_launcher,
)
from .resources import databricks_client
from .solids import create_databricks_job_solid
from .types import (
    DATABRICKS_RUN_TERMINATED_STATES,
    DatabricksRunLifeCycleState,
    DatabricksRunResultState,
)
from .version import __version__

check_dagster_package_version("dagster-databricks", __version__)

__all__ = [
    "create_databricks_job_solid",
    "databricks_client",
    "DatabricksConfig",
    "DatabricksError",
    "DatabricksJobRunner",
    "DatabricksPySparkStepLauncher",
    "databricks_pyspark_step_launcher",
    "DATABRICKS_RUN_TERMINATED_STATES",
    "DatabricksRunLifeCycleState",
    "DatabricksRunResultState",
]
