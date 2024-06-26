"""Databricks integration for Dagster.

This package provides:

- the :py:class:`~dagster_databricks.databricks_pyspark_step_launcher` resource, which
    launches a Databricks job in which an op can be run
- the :py:class:`~dagster_databricks.DatabricksRunJobSolidDefinition`, which can be used
    to execute an arbitrary task in Databricks.
"""

from dagster._core.libraries import DagsterLibraryRegistry

from .pipes import (
    PipesDatabricksClient as PipesDatabricksClient,
    PipesDbfsContextInjector as PipesDbfsContextInjector,
    PipesDbfsLogReader as PipesDbfsLogReader,
    PipesDbfsMessageReader as PipesDbfsMessageReader,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-databricks", __version__)
