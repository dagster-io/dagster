import dagstermill
from dagster import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    PresetDefinition,
    file_relative_path,
    fs_io_manager,
    pipeline,
    repository,
)

from ..data_frame import DataFrame
from .pandas_hello_world.pipeline import pandas_hello_world


def nb_test_path(name):
    return file_relative_path(__file__, "notebooks/{name}.ipynb".format(name=name))


hello_world = dagstermill.define_dagstermill_solid(
    name="papermill_pandas_hello_world",
    notebook_path=nb_test_path("papermill_pandas_hello_world"),
    input_defs=[InputDefinition(name="df", dagster_type=DataFrame)],
    output_defs=[OutputDefinition(DataFrame)],
)


@pipeline(
    mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})],
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
    ],
)
def papermill_pandas_hello_world_pipeline():
    hello_world()


@repository
def test_dagstermill_pandas_solids():
    return [papermill_pandas_hello_world_pipeline, pandas_hello_world]
