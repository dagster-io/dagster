import re

import nbformat
import psycopg2
import pytest
from dagster import seven
from dagster.utils import script_relative_path
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError

valid_notebook_paths = [
    (
        "../../../python_modules/libraries/dagster-pandas/dagster_pandas/examples/notebooks/papermill_pandas_hello_world.ipynb"
    ),
    ("../../../python_modules/dagit/dagit_tests/render_uuid_notebook.ipynb"),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/hello_world_output.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/hello_world.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/tutorial_LR.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/tutorial_RF.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/clean_data.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/add_two_numbers.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/mult_two_numbers.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/hello_logging.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/hello_world_explicit_yield.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/bad_kernel.ipynb"
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/hello_world_resource.ipynb"
    ),
    ("../../../python_modules/libraries/dagstermill/dagstermill_tests/notebooks/retroactive.ipynb"),
    ("../../../docs/sections/learn/guides/data_science/iris-kmeans.ipynb"),
    ("../../../docs/sections/learn/guides/data_science/iris-kmeans_2.ipynb"),
    ("../../../docs/sections/learn/guides/data_science/iris-kmeans_3.ipynb"),
]

invalid_notebook_paths = [
    (
        "../../../python_modules/libraries/dagster-pandas/dagster_pandas/examples/pandas_hello_world/scratch.ipynb",
        ["cells", 0, "outputs", 0],
        seven.ModuleNotFoundError.__name__,
        "No module named 'dagster_contrib'",
        "error",
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/error_notebook.ipynb",
        ["cells", 1, "outputs", 0],
        Exception.__name__,
        "Someone set up us the bomb",
        "error",
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/hello_world_config.ipynb",
        ["cells", 1, "outputs", 0],
        TypeError.__name__,
        "got an unexpected keyword argument 'solid_name'",
        "error",
    ),
    (
        "../../../python_modules/libraries/dagstermill/dagstermill/examples/notebooks/hello_world_resource_with_exception.ipynb",
        ["cells", 4, "outputs", 0],
        Exception.__name__,
        "",
        "error",
    ),
    (
        "../../../airline_demo/airline_demo/notebooks/Delays_by_Geography.ipynb",
        ["cells", 6, "outputs", 0],
        psycopg2.OperationalError.__name__,
        "could not connect to server:",
        "error",
    ),
    (
        "../../../airline_demo/airline_demo/notebooks/SFO_Delays_by_Destination.ipynb",
        ["cells", 6, "outputs", 0],
        psycopg2.OperationalError.__name__,
        "could not connect to server:",
        "error",
    ),
    (
        "../../../airline_demo/airline_demo/notebooks/Fares_vs_Delays.ipynb",
        ["cells", 6, "outputs", 0],
        psycopg2.OperationalError.__name__,
        "could not connect to server:",
        "error",
    ),
]


def get_dict_value(cell_dict, keys):
    if not keys:
        return cell_dict
    return get_dict_value(cell_dict[keys[0]], keys[1:])


@pytest.mark.skip
@pytest.mark.parametrize("valid_notebook_path", valid_notebook_paths)
def test_valid_notebooks(valid_notebook_path):
    notebook_filename = script_relative_path(valid_notebook_path)
    with open(notebook_filename) as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        ep.preprocess(
            nb,
            {
                "metadata": {
                    "path": script_relative_path(notebook_filename[: notebook_filename.rfind("/")])
                }
            },
        )


@pytest.mark.skip
@pytest.mark.parametrize(
    "invalid_notebook_path, cell_location, error_name, error_value, error_output_type",
    invalid_notebook_paths,
)
def test_invalid_notebooks(
    invalid_notebook_path, cell_location, error_name, error_value, error_output_type
):
    notebook_filename = script_relative_path(invalid_notebook_path)
    with open(notebook_filename) as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")

        try:
            ep.preprocess(
                nb,
                {
                    "metadata": {
                        "path": script_relative_path(
                            notebook_filename[: notebook_filename.rfind("/")]
                        )
                    }
                },
            )
        except CellExecutionError:
            error_message = get_dict_value(nb, cell_location)
            assert error_message.ename == error_name
            assert bool(re.search(error_value, error_message.evalue))
            assert error_message.output_type == error_output_type
