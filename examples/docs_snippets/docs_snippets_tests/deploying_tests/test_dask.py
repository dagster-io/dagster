from dagster import execute_pipeline, file_relative_path, reconstructable
from dagster.core.test_utils import instance_for_test
from dagster.utils.yaml_utils import load_yaml_from_globs
from docs_snippets.deploying.dask_hello_world import dask_pipeline  # pylint: disable=import-error


def test_dask_pipeline():
    with instance_for_test() as instance:
        run_config = load_yaml_from_globs(
            file_relative_path(__file__, "../../docs_snippets/deploying/dask_hello_world.yaml")
        )
        result = execute_pipeline(
            reconstructable(dask_pipeline),
            run_config=run_config,
            instance=instance,
        )
        assert result.success
        assert result.result_for_solid("hello_world").output_value() == "Hello, World!"
