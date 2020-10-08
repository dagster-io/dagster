from docs_snippets.deploying.dask_hello_world import dask_pipeline

from dagster import DagsterInstance, execute_pipeline, file_relative_path, reconstructable
from dagster.utils.yaml_utils import load_yaml_from_globs


def test_dask_pipeline():
    run_config = load_yaml_from_globs(
        file_relative_path(__file__, "../../docs_snippets/deploying/dask_hello_world.yaml")
    )
    result = execute_pipeline(
        reconstructable(dask_pipeline),
        run_config=run_config,
        instance=DagsterInstance.local_temp(),
    )
    assert result.success
    assert result.result_for_solid("hello_world").output_value() == "Hello, World!"
