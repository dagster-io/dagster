"""Databricks integration for Dagster.

This package provides:

- the :py:class:`~dagster_databricks.databricks_pyspark_step_launcher` resource, which
    launches a Databricks job in which an op can be run
- the :py:class:`~dagster_databricks.DatabricksRunJobSolidDefinition`, which can be used
    to execute an arbitrary task in Databricks.
"""

from dagster._core.libraries import DagsterLibraryRegistry

from .ops import (
    create_databricks_run_now_op as create_databricks_run_now_op,
    create_databricks_submit_run_op as create_databricks_submit_run_op,
)
from .pipes import (
    PipesDbfsLogReader as PipesDbfsLogReader,
    PipesDatabricksClient as PipesDatabricksClient,
    PipesDbfsMessageReader as PipesDbfsMessageReader,
    PipesDbfsContextInjector as PipesDbfsContextInjector,
)
from .version import __version__
from .resources import (
    DatabricksClientResource as DatabricksClientResource,
    databricks_client as databricks_client,
)
from .databricks import (
    DatabricksError as DatabricksError,
    DatabricksClient as DatabricksClient,
    DatabricksJobRunner as DatabricksJobRunner,
)
from .databricks_pyspark_step_launcher import (
    DatabricksConfig as DatabricksConfig,
    DatabricksPySparkStepLauncher as DatabricksPySparkStepLauncher,
    databricks_pyspark_step_launcher as databricks_pyspark_step_launcher,
)

DagsterLibraryRegistry.register("dagster-databricks", __version__)
