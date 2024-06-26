"""Databricks pipes integration for Dagster.

This package provides:

- the :py:class:`~dagster_databricks_pipes.PipesDatabricksClient` class, which
    makes it possible to create a databricks pipes session
"""

from dagster._core.libraries import DagsterLibraryRegistry

from .pipes import (
    PipesDatabricksClient as PipesDatabricksClient,
    PipesDbfsContextInjector as PipesDbfsContextInjector,
    PipesDbfsLogReader as PipesDbfsLogReader,
    PipesDbfsMessageReader as PipesDbfsMessageReader,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-databricks-pipes", __version__)
