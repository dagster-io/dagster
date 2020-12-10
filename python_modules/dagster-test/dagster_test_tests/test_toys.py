import pytest
from dagster import (
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterTypeCheckDidNotPass,
    execute_pipeline,
)
from dagster.utils.temp_file import get_temp_dir
from dagster_test.toys.composition import composition
from dagster_test.toys.dynamic import dynamic_pipeline
from dagster_test.toys.error_monster import error_monster
from dagster_test.toys.hammer import hammer_pipeline
from dagster_test.toys.log_spew import log_spew
from dagster_test.toys.many_events import many_events
from dagster_test.toys.pyspark_assets.pyspark_assets_pipeline import pyspark_assets_pipeline
from dagster_test.toys.repo import toys_repository
from dagster_test.toys.resources import resource_pipeline
from dagster_test.toys.sleepy import sleepy_pipeline


def test_repo():
    assert toys_repository


def test_dynamic_pipeline():
    assert execute_pipeline(dynamic_pipeline).success


def test_many_events_pipeline():
    assert execute_pipeline(many_events).success


def test_sleepy_pipeline():
    assert execute_pipeline(sleepy_pipeline).success


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
                    "config": {"temperature_file": "temperature.csv", "version_salt": "foo",}
                },
                "get_consolidated_location": {
                    "config": {"station_file": "stations.csv", "version_salt": "foo",}
                },
                "combine_dfs": {"config": {"version_salt": "foo",}},
                "pretty_output": {"config": {"version_salt": "foo",}},
            },
            "resources": {
                "source_data_dir": {
                    "config": {
                        "dir": "python_modules/dagster-test/dagster_test/toys/pyspark_assets/asset_pipeline_files"
                    }
                },
                "savedir": {"config": {"dir": temp_dir}},
            },
        }

        result = execute_pipeline(pyspark_assets_pipeline, run_config=run_config,)
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
        composition, run_config={"solids": {"add_four": {"inputs": {"num": 3}}}},
    )

    assert result.success

    assert result.output_for_solid("div_four") == 7.0 / 4.0
