import pytest
from dagster_test.toys.asset_lineage import asset_lineage_pipeline
from dagster_test.toys.composition import composition
from dagster_test.toys.dynamic import dynamic_pipeline
from dagster_test.toys.error_monster import error_monster
from dagster_test.toys.hammer import hammer_pipeline
from dagster_test.toys.log_spew import log_spew
from dagster_test.toys.longitudinal import IntentionalRandomFailure, longitudinal_pipeline
from dagster_test.toys.many_events import many_events
from dagster_test.toys.notebooks import hello_world_notebook_pipeline
from dagster_test.toys.pyspark_assets.pyspark_assets_pipeline import pyspark_assets_pipeline
from dagster_test.toys.repo import toys_repository
from dagster_test.toys.resources import resource_pipeline
from dagster_test.toys.retries import retry_pipeline
from dagster_test.toys.schedules import longitudinal_schedule
from dagster_test.toys.sleepy import sleepy_pipeline

from dagster import (
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterTypeCheckDidNotPass,
    execute_pipeline,
    reconstructable,
)
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path
from dagster._utils.temp_file import get_temp_dir


def test_repo():
    assert toys_repository


def test_dynamic_pipeline():
    assert execute_pipeline(dynamic_pipeline).success


def test_longitudinal_pipeline():
    partition_set = longitudinal_schedule().get_partition_set()
    try:
        result = execute_pipeline(
            longitudinal_pipeline,
            run_config=partition_set.run_config_for_partition(partition_set.get_partitions()[0]),
        )
        assert result.success
    except IntentionalRandomFailure:
        pass


def test_many_events_pipeline():
    assert execute_pipeline(many_events).success


def get_sleepy():
    return sleepy_pipeline


def test_sleepy_pipeline():
    with instance_for_test() as instance:
        assert execute_pipeline(reconstructable(get_sleepy), instance=instance).success


def test_spew_pipeline():
    assert execute_pipeline(log_spew).success


def test_hammer_pipeline():
    assert execute_pipeline(hammer_pipeline).success


def test_resource_pipeline_no_config():
    result = execute_pipeline(resource_pipeline)
    assert result.result_for_solid("one").output_value() == 2


def test_resource_pipeline_with_config():
    result = execute_pipeline(resource_pipeline, run_config={"resources": {"R1": {"config": 2}}})
    assert result.result_for_solid("one").output_value() == 3


def test_pyspark_assets_pipeline():

    with get_temp_dir() as temp_dir:
        run_config = {
            "solids": {
                "get_max_temp_per_station": {
                    "config": {
                        "temperature_file": "temperature.csv",
                        "version_salt": "foo",
                    }
                },
                "get_consolidated_location": {
                    "config": {
                        "station_file": "stations.csv",
                        "version_salt": "foo",
                    }
                },
                "combine_dfs": {
                    "config": {
                        "version_salt": "foo",
                    }
                },
                "pretty_output": {
                    "config": {
                        "version_salt": "foo",
                    }
                },
            },
            "resources": {
                "source_data_dir": {
                    "config": {
                        "dir": file_relative_path(
                            __file__, "../dagster_test/toys/pyspark_assets/asset_pipeline_files"
                        ),
                    }
                },
                "savedir": {"config": {"dir": temp_dir}},
            },
        }

        result = execute_pipeline(
            pyspark_assets_pipeline,
            run_config=run_config,
        )
        assert result.success


def test_error_monster_success():
    assert execute_pipeline(
        error_monster,
        run_config={
            "solids": {
                "start": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                "middle": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                "end": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
            },
            "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
        },
    ).success

    assert execute_pipeline(
        pipeline=error_monster,
        mode="errorable_mode",
        run_config={
            "solids": {
                "start": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                "middle": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                "end": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
            },
            "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
        },
    ).success


def test_error_monster_wrong_mode():
    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            pipeline=error_monster,
            mode="nope",
            run_config={
                "solids": {
                    "start": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                    "middle": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                    "end": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                },
                "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
            },
        )


def test_error_monster_success_error_on_resource():
    with pytest.raises(DagsterResourceFunctionError):
        execute_pipeline(
            error_monster,
            run_config={
                "solids": {
                    "start": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                    "middle": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                    "end": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                },
                "resources": {"errorable_resource": {"config": {"throw_on_resource_init": True}}},
            },
        )


def test_error_monster_type_error():
    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_pipeline(
            error_monster,
            run_config={
                "solids": {
                    "start": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                    "middle": {"config": {"throw_in_solid": False, "return_wrong_type": True}},
                    "end": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                },
                "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
            },
        )


def test_composition_pipeline():
    result = execute_pipeline(
        composition,
        run_config={"solids": {"add_four": {"inputs": {"num": 3}}}},
    )

    assert result.success

    assert result.output_for_solid("div_four") == 7.0 / 4.0


def test_asset_lineage_pipeline():
    assert execute_pipeline(
        asset_lineage_pipeline,
        run_config={
            "solids": {
                "download_data": {"outputs": {"result": {"partitions": ["2020-01-01"]}}},
                "split_action_types": {
                    "outputs": {
                        "comments": {"partitions": ["2020-01-01"]},
                        "reviews": {"partitions": ["2020-01-01"]},
                    }
                },
                "top_10_comments": {"outputs": {"result": {"partitions": ["2020-01-01"]}}},
                "top_10_reviews": {"outputs": {"result": {"partitions": ["2020-01-01"]}}},
            }
        },
    ).success


def test_retry_pipeline():
    assert execute_pipeline(
        retry_pipeline,
        run_config=retry_pipeline.get_preset("pass_after_retry").run_config,
    ).success


def test_notebook_pipeline():
    with instance_for_test() as instance:
        assert execute_pipeline(
            reconstructable(hello_world_notebook_pipeline),
            instance=instance,
        ).success
