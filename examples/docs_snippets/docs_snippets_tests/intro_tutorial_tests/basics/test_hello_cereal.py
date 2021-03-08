from dagster import execute_pipeline
from dagster.utils import check_cli_execute_file_pipeline, pushd, script_relative_path
from docs_snippets.intro_tutorial.basics.single_solid_pipeline.hello_cereal import (
    hello_cereal_pipeline,
)


def test_tutorial_intro_tutorial_hello_world():
    with pushd(
        script_relative_path("../../../docs_snippets/intro_tutorial/basics/single_solid_pipeline/")
    ):
        result = execute_pipeline(hello_cereal_pipeline)

    assert result.success


def test_tutorial_intro_tutorial_hello_world_cli():
    check_cli_execute_file_pipeline(
        script_relative_path(
            "../../../docs_snippets/intro_tutorial/basics/single_solid_pipeline//hello_cereal.py"
        ),
        "hello_cereal_pipeline",
    )
