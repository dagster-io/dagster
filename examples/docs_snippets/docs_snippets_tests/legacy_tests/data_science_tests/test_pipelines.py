import pytest

from dagster import DagsterInstance, execute_pipeline, file_relative_path
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.utils import pushd
from dagster.utils.yaml_utils import load_yaml_from_path


@pytest.mark.parametrize(
    "file_path,run_config_path",
    [
        ["iris_pipeline.py", None,],
        ["iris_pipeline_2.py", "iris_pipeline_dev.yaml",],
        ["iris_pipeline_3.py", "iris_pipeline_dev.yaml",],
    ],
)
def test_pipelines_success(file_path, run_config_path):

    with pushd(file_relative_path(__file__, "../../../docs_snippets/legacy/data_science/")):
        instance = DagsterInstance.local_temp()
        run_config = load_yaml_from_path(run_config_path) if run_config_path else None
        recon_pipeline = ReconstructablePipeline.for_file(file_path, "iris_pipeline")

        pipeline_result = execute_pipeline(
            recon_pipeline,
            run_config=run_config,
            instance=instance,
            solid_selection=["k_means_iris"],  # skip download_file in tests
        )
        assert pipeline_result.success
