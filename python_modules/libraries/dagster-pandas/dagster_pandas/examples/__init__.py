import sys

import pandas as pd
import pytest

import dagstermill

from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    PresetDefinition,
    execute_pipeline,
    file_relative_path,
)

from dagster.core.utility_solids import define_stub_solid

from dagster.utils import script_relative_path

from ..data_frame import DataFrame

from .pandas_hello_world.pipeline import define_pandas_hello_world_pipeline


def nb_test_path(name):
    return script_relative_path('notebooks/{name}.ipynb'.format(name=name))


def define_papermill_pandas_hello_world_solid():
    return dagstermill.define_dagstermill_solid(
        name='papermill_pandas_hello_world',
        notebook_path=nb_test_path('papermill_pandas_hello_world'),
        input_defs=[InputDefinition(name='df', dagster_type=DataFrame)],
        output_defs=[OutputDefinition(DataFrame)],
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
        solid_defs=[define_papermill_pandas_hello_world_solid()],
        preset_defs=[
            PresetDefinition(
                'test',
                environment_files=[
                    file_relative_path(
                        __file__,
                        'pandas_hello_world/environments/papermill_pandas_hello_world_test.yaml',
                    )
                ],
            ),
            PresetDefinition(
                'prod',
                environment_files=[
                    file_relative_path(
                        __file__,
                        'pandas_hello_world/environments/papermill_pandas_hello_world_prod.yaml',
                    )
                ],
            ),
        ],
    )
