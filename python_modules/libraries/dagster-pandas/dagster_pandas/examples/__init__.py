import sys

import dagstermill
import pandas as pd
import pytest
from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PresetDefinition,
    execute_pipeline,
    file_relative_path,
    pipeline,
    repository,
)
from dagster.core.utility_solids import define_stub_solid

from ..data_frame import DataFrame
from .pandas_hello_world.pipeline import pandas_hello_world


def nb_test_path(name):
    return file_relative_path(__file__, "notebooks/{name}.ipynb".format(name=name))


def define_papermill_pandas_hello_world_solid():
    return dagstermill.define_dagstermill_solid(
        name="papermill_pandas_hello_world",
        notebook_path=nb_test_path("papermill_pandas_hello_world"),
        input_defs=[InputDefinition(name="df", dagster_type=DataFrame)],
        output_defs=[OutputDefinition(DataFrame)],
    )


@pipeline(
    preset_defs=[
        PresetDefinition.from_files(
            "test",
            config_files=[
                file_relative_path(
                    __file__,
                    "pandas_hello_world/environments/papermill_pandas_hello_world_test.yaml",
                )
            ],
        ),
        PresetDefinition.from_files(
            "prod",
            config_files=[
                file_relative_path(
                    __file__,
                    "pandas_hello_world/environments/papermill_pandas_hello_world_prod.yaml",
                )
            ],
        ),
    ]
)
def papermill_pandas_hello_world_pipeline():
    hello_world = define_papermill_pandas_hello_world_solid()
    hello_world()


@repository
def test_dagstermill_pandas_solids():
    return [papermill_pandas_hello_world_pipeline, pandas_hello_world]
