import tempfile

import pytest

from dagster import execute_job, file_relative_path
from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.test_utils import instance_for_test
from dagster._legacy import execute_pipeline
from dagster._utils import pushd
from dagster._utils.yaml_utils import load_yaml_from_path


@pytest.mark.parametrize(
    "file_path,run_config_path",
    [
        [
            "iris_classify.py",
            None,
        ],
        [
            "iris_classify_2.py",
            "iris_classify_dev.yaml",
        ],
        [
            "iris_classify_3.py",
            "iris_classify_dev.yaml",
        ],
    ],
)
def test_pipelines_success(file_path, run_config_path):

    with pushd(
        file_relative_path(__file__, "../../../docs_snippets/legacy/data_science/")
    ):
        with instance_for_test() as instance:
            run_config = load_yaml_from_path(run_config_path) if run_config_path else {}
            recon_pipeline = ReconstructablePipeline.for_file(
                file_path, "iris_classify"
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                run_config["resources"] = {
                    "io_manager": {"config": {"base_dir": temp_dir}}
                }
                result = execute_job(
                    recon_pipeline,
                    instance,
                    run_config=run_config,
                    op_selection=["k_means_iris"],  # skip download_file in tests
                )

                assert result.success
