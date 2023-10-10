"""Databricks integration for Dagster.

This package provides:

- the :py:class:`~dagster_databricks.databricks_pyspark_step_launcher` resource, which
    launches a Databricks job in which an op can be run
- the :py:class:`~dagster_databricks.DatabricksRunJobSolidDefinition`, which can be used
    to execute an arbitrary task in Databricks.
"""

from dagster._core.libraries import DagsterLibraryRegistry

from .databricks import (
    DatabricksClient as DatabricksClient,
    DatabricksError as DatabricksError,
    DatabricksJobRunner as DatabricksJobRunner,
)
from .databricks_pyspark_step_launcher import (
    DatabricksConfig as DatabricksConfig,
    DatabricksPySparkStepLauncher as DatabricksPySparkStepLauncher,
    databricks_pyspark_step_launcher as databricks_pyspark_step_launcher,
)
from .ops import (
    create_databricks_run_now_op as create_databricks_run_now_op,
    create_databricks_submit_run_op as create_databricks_submit_run_op,
)
from .pipes import (
    PipesDatabricksClient as PipesDatabricksClient,
    PipesDbfsContextInjector as PipesDbfsContextInjector,
    PipesDbfsMessageReader as PipesDbfsMessageReader,
)
from .resources import (
    DatabricksClientResource as DatabricksClientResource,
    databricks_client as databricks_client,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-databricks", __version__)
