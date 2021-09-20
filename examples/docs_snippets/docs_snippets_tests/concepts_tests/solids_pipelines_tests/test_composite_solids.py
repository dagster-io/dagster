import yaml
from dagster import execute_pipeline
from dagster.utils import file_relative_path
from docs_snippets.concepts.solids_pipelines.composite_solids import (
    my_pipeline,
    my_pipeline_composite_config,
    my_pipeline_config_mapping,
    my_pipeline_multi_outputs,
)


def test_composite_def_example():
    assert execute_pipeline(my_pipeline).success


def test_composite_config_example():
    with open(
        file_relative_path(
            __file__, "../../../docs_snippets/concepts/solids_pipelines/composite_config.yaml"
        ),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())

    assert execute_pipeline(my_pipeline_composite_config, run_config=run_config).success


def test_config_mapping_example():
    with open(
        file_relative_path(
            __file__,
            "../../../docs_snippets/concepts/solids_pipelines/composite_config_mapping.yaml",
        ),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())

    assert execute_pipeline(my_pipeline_config_mapping, run_config=run_config).success


def test_composite_multi_outputs_example():
    assert execute_pipeline(my_pipeline_multi_outputs).success
