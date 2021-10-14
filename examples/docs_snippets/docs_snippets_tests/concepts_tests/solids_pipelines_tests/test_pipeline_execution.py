import yaml
from dagster import execute_pipeline, reconstructable
from dagster.core.test_utils import instance_for_test
from dagster.utils import file_relative_path
from docs_snippets.concepts.solids_pipelines.pipeline_execution import (
    execute_multiprocessing,
    execute_subset,
    my_pipeline,
    parallel_pipeline,
)


def test_execute_my_pipeline():
    result = execute_pipeline(my_pipeline)
    assert result.success


def test_solid_selection():
    execute_subset()


def test_multiprocess_yaml():
    with open(
        file_relative_path(
            __file__, "../../../docs_snippets/concepts/solids_pipelines/multiprocessing.yaml"
        ),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())

    with instance_for_test() as instance:
        assert execute_pipeline(
            reconstructable(parallel_pipeline), run_config=run_config, instance=instance
        ).success


def test_multiprocess_pipeline():
    execute_multiprocessing()
