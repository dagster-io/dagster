import tempfile

from dagster import execute_pipeline
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.test_utils import instance_for_test

CEREALS_DATASET_URL = "https://gist.githubusercontent.com/mgasner/bd2c0f66dff4a9f01855cfa6870b1fce/raw/2de62a57fb08da7c58d6480c987077cf91c783a1/cereal.csv"


def test_pipeline(pg_hostname, postgres):  # pylint: disable=unused-argument
    reconstructable_pipeline = ReconstructablePipeline.for_module(
        "dbt_example", "dbt_example_pipeline"
    )
    assert set([solid.name for solid in reconstructable_pipeline.get_definition().solids]) == {
        "download_file",
        "load_cereals_from_csv",
        "run_cereals_models",
        "test_cereals_models",
        "analyze_cereals",
        "post_plot_to_slack",
    }
    with instance_for_test() as instance:
        with tempfile.TemporaryDirectory() as temp_dir:
            res = execute_pipeline(
                ReconstructablePipeline.for_module("dbt_example", "dbt_example_pipeline"),
                instance=instance,
                mode="dev",
                run_config={
                    "solids": {
                        "download_file": {
                            "config": {
                                "url": CEREALS_DATASET_URL,
                                "target_path": "cereals.csv",
                            }
                        },
                        "post_plot_to_slack": {"config": {"channels": ["foo_channel"]}},
                    },
                    "resources": {
                        "db": {
                            "config": {
                                "db_url": (
                                    f"postgresql://dbt_example:dbt_example@{pg_hostname}"
                                    ":5432/dbt_example"
                                )
                            }
                        },
                        "slack": {"config": {"token": "nonce"}},
                        "io_manager": {"config": {"base_dir": temp_dir}},
                    },
                },
            )
            assert res.success
