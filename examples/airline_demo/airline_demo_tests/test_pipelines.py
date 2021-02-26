import os
import tempfile

# pylint: disable=unused-argument
import pytest
from dagster import execute_pipeline, file_relative_path
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.test_utils import instance_for_test
from dagster.utils import load_yaml_from_globs

ingest_pipeline = ReconstructablePipeline.for_module(
    "airline_demo.pipelines",
    "define_airline_demo_ingest_pipeline",
)

warehouse_pipeline = ReconstructablePipeline.for_module(
    "airline_demo.pipelines",
    "define_airline_demo_warehouse_pipeline",
)


def config_path(relative_path):
    return file_relative_path(
        __file__, os.path.join("../airline_demo/environments/", relative_path)
    )


@pytest.mark.db
@pytest.mark.nettest
@pytest.mark.py3
@pytest.mark.spark
def test_ingest_pipeline_fast(postgres, pg_hostname):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test() as instance:
            ingest_config_dict = load_yaml_from_globs(
                config_path("test_base.yaml"),
                config_path("local_fast_ingest.yaml"),
            )
            ingest_config_dict["resources"]["io_manager"] = {"config": {"base_dir": temp_dir}}
            ingest_config_dict["resources"]["pyspark_io_manager"] = {
                "config": {"base_dir": temp_dir}
            }
            result_ingest = execute_pipeline(
                pipeline=ingest_pipeline,
                mode="local",
                run_config=ingest_config_dict,
                instance=instance,
            )

            assert result_ingest.success


@pytest.mark.db
@pytest.mark.nettest
@pytest.mark.py3
@pytest.mark.spark
@pytest.mark.skipif('"win" in sys.platform', reason="avoiding the geopandas tests")
def test_airline_pipeline_1_warehouse(postgres, pg_hostname):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test() as instance:

            warehouse_config_object = load_yaml_from_globs(
                config_path("test_base.yaml"), config_path("local_warehouse.yaml")
            )
            warehouse_config_object["resources"]["io_manager"] = {"config": {"base_dir": temp_dir}}
            warehouse_config_object["resources"]["pyspark_io_manager"] = {
                "config": {"base_dir": temp_dir}
            }
            result_warehouse = execute_pipeline(
                pipeline=warehouse_pipeline,
                mode="local",
                run_config=warehouse_config_object,
                instance=instance,
            )
            assert result_warehouse.success
