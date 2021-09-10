import dagstermill
from dagster import (
    In,
    Out,
    InputDefinition,
    OutputDefinition,
    config_from_files,
    file_relative_path,
    fs_io_manager,
    graph,
    repository,
)

from ..data_frame import DataFrame
from .pandas_hello_world.job import pandas_hello_world


def nb_test_path(name):
    return file_relative_path(__file__, "notebooks/{name}.ipynb".format(name=name))


hello_world = dagstermill.define_dagstermill_solid(
    name="papermill_pandas_hello_world",
    notebook_path=nb_test_path("papermill_pandas_hello_world"),
    input_defs=[InputDefinition(name="df", dagster_type=DataFrame)],
    output_defs=[OutputDefinition(DataFrame)],
)


@graph
def papermill_pandas_hello_world():
    hello_world()


papermill_pandas_hello_world_test = papermill_pandas_hello_world.to_job(
    resource_defs={"io_manager": fs_io_manager},
    config=config_from_files(
        [
            file_relative_path(
                __file__,
                "pandas_hello_world/environments/papermill_pandas_hello_world_test.yaml",
            )
        ]
    ),
)

papermill_pandas_hello_world_prod = papermill_pandas_hello_world.to_job(
    resource_defs={"io_manager": fs_io_manager},
    config=config_from_files(
        [
            file_relative_path(
                __file__,
                "pandas_hello_world/environments/papermill_pandas_hello_world_prod.yaml",
            )
        ]
    ),
)


@repository
def test_dagstermill_pandas():
    return [papermill_pandas_hello_world_prod, pandas_hello_world]
