import tempfile

import pytest
from dagster import execute_pipeline, file_relative_path
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.test_utils import instance_for_test
from dagster.utils import pushd
from dagster.utils.yaml_utils import load_yaml_from_path


@pytest.mark.parametrize(
    "file_path,run_config_path",
    [
        [
            "iris_pipeline.py",
            None,
        ],
        [
            "iris_pipeline_2.py",
            "iris_pipeline_dev.yaml",
        ],
        [
            "iris_pipeline_3.py",
            "iris_pipeline_dev.yaml",
        ],
    ],
)
def test_pipelines_success(file_path, run_config_path):

    with pushd(file_relative_path(__file__, "../../../docs_snippets/legacy/data_science/")):
        with instance_for_test() as instance:
            run_config = load_yaml_from_path(run_config_path) if run_config_path else {}
            recon_pipeline = ReconstructablePipeline.for_file(file_path, "iris_pipeline")

            with tempfile.TemporaryDirectory() as temp_dir:
                run_config["resources"] = {"io_manager": {"config": {"base_dir": temp_dir}}}
                pipeline_result = execute_pipeline(
                    recon_pipeline,
                    run_config=run_config,
                    instance=instance,
                    solid_selection=["k_means_iris"],  # skip download_file in tests
                )
                assert pipeline_result.success
