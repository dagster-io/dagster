import tempfile

import pandas as pd
from dagster import execute_pipeline
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.test_utils import instance_for_test
from dagster.utils import file_relative_path


def test_papermill_pandas_hello_world_pipeline():
    pipeline = ReconstructablePipeline.for_module(
        "dagster_pandas.examples", "papermill_pandas_hello_world_pipeline"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test() as instance:
            pipeline_result = execute_pipeline(
                pipeline,
                {
                    "solids": {
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
            )
            assert pipeline_result.success
            solid_result = pipeline_result.result_for_solid("papermill_pandas_hello_world")
            expected = pd.read_csv(file_relative_path(__file__, "num_prod.csv")) + 1
            assert solid_result.output_value().equals(expected)
