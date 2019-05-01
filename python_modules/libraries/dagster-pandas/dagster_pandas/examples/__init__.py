import sys

import pandas as pd
import pytest

import dagstermill as dm

from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    execute_pipeline,
    types,
)

from dagster.core.utility_solids import define_stub_solid

from dagster.utils import script_relative_path

from ..data_frame import DataFrame

from .pandas_hello_world.pipeline import define_pandas_hello_world_pipeline


def nb_test_path(name):
    return script_relative_path('notebooks/{name}.ipynb'.format(name=name))


def define_papermill_pandas_hello_world_solid():
    return dm.define_dagstermill_solid(
        name='papermill_pandas_hello_world',
        notebook_path=nb_test_path('papermill_pandas_hello_world'),
        inputs=[InputDefinition(name='df', dagster_type=DataFrame)],
        outputs=[OutputDefinition(DataFrame)],
    )


def define_pandas_repository():
    return RepositoryDefinition(
        name='test_dagstermill_pandas_solids',
        pipeline_dict={
            'papermill_pandas_hello_world_pipeline': define_papermill_pandas_hello_world_pipeline,
            'pandas_hello_world': define_pandas_hello_world_pipeline,
        },
    )


def define_papermill_pandas_hello_world_pipeline():
    return PipelineDefinition(
        name='papermill_pandas_hello_world_pipeline',
        solids=[define_papermill_pandas_hello_world_solid()],
    )
