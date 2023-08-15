import tempfile

import pandas as pd
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.execution.api import execute_job
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path


def test_papermill_pandas_hello_world_job():
    recon_job = ReconstructableJob.for_module(
        "dagster_pandas.examples", "papermill_pandas_hello_world_test"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test() as instance:
            with execute_job(
                recon_job,
                run_config={
                    "ops": {
                        "papermill_pandas_hello_world": {
                            "inputs": {
                                "df": {
                                    "csv": {"path": file_relative_path(__file__, "num_prod.csv")}
                                }
                            },
                        }
                    },
                    "resources": {
                        "io_manager": {
                            "config": {"base_dir": temp_dir},
                        },
                    },
                },
                instance=instance,
            ) as result:
                assert result.success
                expected = pd.read_csv(file_relative_path(__file__, "num_prod.csv")) + 1
                assert result.output_for_node("papermill_pandas_hello_world").equals(expected)
