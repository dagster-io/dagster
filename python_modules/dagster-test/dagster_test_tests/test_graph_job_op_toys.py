import pytest
from dagster_test.graph_job_op_toys.asset_lineage import asset_lineage_job
from dagster_test.graph_job_op_toys.branches import branch
from dagster_test.graph_job_op_toys.composition import composition_job
from dagster_test.graph_job_op_toys.dynamic import dynamic
from dagster_test.graph_job_op_toys.error_monster import (
    define_errorable_resource,
    error_monster,
    errorable_io_manager,
)
from dagster_test.graph_job_op_toys.hammer import hammer
from dagster_test.graph_job_op_toys.log_spew import log_spew
from dagster_test.graph_job_op_toys.longitudinal import IntentionalRandomFailure, longitudinal
from dagster_test.graph_job_op_toys.many_events import many_events
from dagster_test.graph_job_op_toys.partitioned_assets import partitioned_asset_group
from dagster_test.graph_job_op_toys.pyspark_assets.pyspark_assets_job import (
    dir_resources,
    pyspark_assets,
)
from dagster_test.graph_job_op_toys.repo import toys_repository
from dagster_test.graph_job_op_toys.resources import lots_of_resources, resource_ops
from dagster_test.graph_job_op_toys.retries import retry
from dagster_test.graph_job_op_toys.schedules import longitudinal_schedule
from dagster_test.graph_job_op_toys.sleepy import sleepy
from dagster_test.graph_job_op_toys.software_defined_assets import software_defined_assets
from dagster_tests.execution_tests.engine_tests.test_step_delegating_executor import (
    test_step_delegating_executor,
)

from dagster import DagsterResourceFunctionError, DagsterTypeCheckDidNotPass, multiprocess_executor
from dagster.core.events import DagsterEventType
from dagster.core.storage.fs_io_manager import fs_io_manager
from dagster._utils import file_relative_path
from dagster._utils.temp_file import get_temp_dir


@pytest.fixture(name="executor_def", params=[multiprocess_executor, test_step_delegating_executor])
def executor_def_fixture(request):
    return request.param


def test_repo():
    assert toys_repository


def test_dynamic_job(executor_def):
    assert dynamic.to_job(executor_def=executor_def).execute_in_process().success


def test_longitudinal_job(executor_def):
    partition_set = longitudinal_schedule().get_partition_set()
    try:
        result = longitudinal.to_job(
            resource_defs={"io_manager": fs_io_manager},
            executor_def=executor_def,
        ).execute_in_process(
            run_config=partition_set.run_config_for_partition(partition_set.get_partitions()[0]),
        )
        assert result.success
    except IntentionalRandomFailure:
        pass


def test_many_events_job(executor_def):
    assert many_events.to_job(executor_def=executor_def).execute_in_process().success


def test_many_events_subset_job(executor_def):
    result = many_events.to_job(
        op_selection=["many_materializations_and_passing_expectations*"], executor_def=executor_def
    ).execute_in_process()
    assert result.success

    executed_step_keys = [
        evt.step_key
        for evt in result.all_node_events
        if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]
    assert len(executed_step_keys) == 3


def test_sleepy_job(executor_def):
    assert (
        lambda: sleepy.to_job(
            config={
                "ops": {"giver": {"config": [2, 2, 2, 2]}},
            },
            executor_def=executor_def,
        )
        .execute_in_process()
        .success
    )


def test_branch_job(executor_def):
    assert (
        branch.to_job(
            config={
                "ops": {"root": {"config": {"sleep_secs": [0, 10]}}},
            },
            executor_def=executor_def,
        )
        .execute_in_process()
        .success
    )


def test_branch_job_failed(executor_def):
    with pytest.raises(Exception):
        assert (
            not branch.to_job(
                name="branch_failed",
                config={
                    "ops": {"root": {"config": {"sleep_secs": [-10, 30]}}},
                },
                executor_def=executor_def,
            )
            .execute_in_process()
            .success
        )


def test_spew_pipeline(executor_def):
    assert log_spew.to_job(executor_def=executor_def).execute_in_process().success


def test_hammer_job(executor_def):
    assert hammer.to_job(executor_def=executor_def).execute_in_process().success


def test_resource_job_no_config(executor_def):
    result = resource_ops.to_job(
        resource_defs=lots_of_resources, executor_def=executor_def
    ).execute_in_process()
    assert result.output_for_node("one") == 2


def test_resource_job_with_config(executor_def):
    result = resource_ops.to_job(
        config={"resources": {"R1": {"config": 2}}},
        resource_defs=lots_of_resources,
        executor_def=executor_def,
    ).execute_in_process()
    assert result.output_for_node("one") == 3


def test_pyspark_assets_job(executor_def):
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
                            __file__,
                            "../dagster_test/graph_job_op_toys/pyspark_assets/asset_job_files",
                        ),
                    }
                },
                "savedir": {"config": {"dir": temp_dir}},
            },
        }

        result = pyspark_assets.to_job(
            config=run_config, resource_defs=dir_resources, executor_def=executor_def
        ).execute_in_process()
        assert result.success


def test_error_monster_success(executor_def):
    assert (
        error_monster.to_job(
            resource_defs={
                "errorable_resource": define_errorable_resource(),
                "io_manager": errorable_io_manager,
            },
            config={
                "ops": {
                    "start": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                    "middle": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                    "end": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                },
                "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
            },
            executor_def=executor_def,
        )
        .execute_in_process()
        .success
    )


def test_error_monster_success_error_on_resource(executor_def):
    with pytest.raises(DagsterResourceFunctionError):
        error_monster.to_job(
            resource_defs={
                "errorable_resource": define_errorable_resource(),
                "io_manager": errorable_io_manager,
            },
            config={
                "ops": {
                    "start": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                    "middle": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                    "end": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                },
                "resources": {"errorable_resource": {"config": {"throw_on_resource_init": True}}},
            },
            executor_def=executor_def,
        ).execute_in_process()


def test_error_monster_type_error(executor_def):
    with pytest.raises(DagsterTypeCheckDidNotPass):
        error_monster.to_job(
            resource_defs={
                "errorable_resource": define_errorable_resource(),
                "io_manager": errorable_io_manager,
            },
            config={
                "ops": {
                    "start": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                    "middle": {"config": {"throw_in_op": False, "return_wrong_type": True}},
                    "end": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                },
                "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
            },
            executor_def=executor_def,
        ).execute_in_process()


def test_composition_job():
    result = composition_job.execute_in_process(
        run_config={"solids": {"add_four": {"inputs": {"num": {"value": 3}}}}},
    )

    assert result.success
    assert result.output_for_node("div_four") == 7.0 / 4.0


def test_asset_lineage_job():
    assert asset_lineage_job.execute_in_process(
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


def test_retry_job(executor_def):
    assert (
        retry.to_job(
            config={
                "ops": {
                    "retry_op": {
                        "config": {
                            "delay": 0.2,
                            "work_on_attempt": 2,
                            "max_retries": 1,
                        }
                    }
                }
            },
            executor_def=executor_def,
        )
        .execute_in_process()
        .success
    )


def test_software_defined_assets_job():
    assert software_defined_assets.build_job("all_assets").execute_in_process().success


def test_partitioned_assets():
    for job_def in partitioned_asset_group.get_base_jobs():
        partition_key = job_def.mode_definitions[
            0
        ].partitioned_config.partitions_def.get_partition_keys()[0]
        assert job_def.execute_in_process(partition_key=partition_key).success
