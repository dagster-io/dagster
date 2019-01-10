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
    define_stub_solid,
    execute_pipeline,
    types,
)

from dagster.utils import script_relative_path

from ..data_frame import DataFrame

from .pandas_hello_world.pipeline import define_success_pipeline


def nb_test_path(name):
    return script_relative_path('notebooks/{name}.ipynb'.format(name=name))


def define_pandas_input_transform_test_solid():
    return dm.define_dagstermill_solid(
        name='pandas_input_transform_test',
        notebook_path=nb_test_path('pandas_input_transform_test'),
        inputs=[InputDefinition('df', DataFrame)],
        outputs=[OutputDefinition(types.Int)],
    )


def define_pandas_input_transform_test_pipeline():
    in_df = pd.DataFrame({'num': [3, 5, 7]})
    return PipelineDefinition(
        name='input_transform_test_pipeline',
        solids=[define_stub_solid('load_df', in_df), define_pandas_input_transform_test_solid()],
        dependencies={'pandas_input_transform_test': {'df': DependencyDefinition('load_df')}},
    )


def define_pandas_source_test_solid():
    return dm.define_dagstermill_solid(
        name='pandas_source_test',
        notebook_path=nb_test_path('pandas_source_test'),
        inputs=[InputDefinition(name='df', dagster_type=DataFrame)],
        outputs=[OutputDefinition(DataFrame)],
    )


def define_pandas_repository():
    return RepositoryDefinition(
        name='test_dagstermill_pandas_solids',
        pipeline_dict={
            'input_transform_test_pipeline': define_pandas_source_test_pipeline,
            'pandas_hello_world': define_success_pipeline,
        },
    )


def define_pandas_source_test_pipeline():
    return PipelineDefinition(
        name='input_transform_test_pipeline',
        solids=[
            define_stub_solid(
                'load_num_csv', pd.read_csv(script_relative_path('data/num_prod.csv'))
            ),
            define_pandas_source_test_solid(),
        ],
        dependencies={'pandas_source_test': {'df': DependencyDefinition('load_num_csv')}},
    )
