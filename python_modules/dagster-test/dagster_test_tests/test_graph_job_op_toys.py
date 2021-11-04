import pytest
from dagster import (
    DagsterResourceFunctionError,
    DagsterTypeCheckDidNotPass,
    execute_pipeline,
    reconstructable,
)
from dagster.core.events import DagsterEventType
from dagster.core.test_utils import instance_for_test
from dagster.utils import file_relative_path
from dagster.utils.temp_file import get_temp_dir
from dagster_test.graph_job_op_toys.asset_lineage import asset_lineage_job
from dagster_test.graph_job_op_toys.branches import branch_failed_job, branch_job
from dagster_test.graph_job_op_toys.composition import composition_job
from dagster_test.graph_job_op_toys.dynamic import dynamic_job
from dagster_test.graph_job_op_toys.error_monster import (
    define_errorable_resource,
    error_monster,
    errorable_io_manager,
)
from dagster_test.graph_job_op_toys.hammer import hammer_default_executor_job
from dagster_test.graph_job_op_toys.log_spew import log_spew_job
from dagster_test.graph_job_op_toys.longitudinal import IntentionalRandomFailure, longitudinal_job
from dagster_test.graph_job_op_toys.many_events import many_events_job, many_events_subset_job
from dagster_test.graph_job_op_toys.pyspark_assets.pyspark_assets_job import (
    dir_resources,
    pyspark_assets,
)
from dagster_test.graph_job_op_toys.repo import toys_repository
from dagster_test.graph_job_op_toys.resources import lots_of_resources, resource_job, resource_ops
from dagster_test.graph_job_op_toys.retries import retry_job
from dagster_test.graph_job_op_toys.schedules import longitudinal_schedule
from dagster_test.graph_job_op_toys.sleepy import sleepy_job


def test_repo():
    assert toys_repository


def test_dynamic_job():
    assert dynamic_job.execute_in_process().success


def test_longitudinal_job():
    partition_set = longitudinal_schedule().get_partition_set()
    try:
        result = longitudinal_job.execute_in_process(
            run_config=partition_set.run_config_for_partition(partition_set.get_partitions()[0]),
        )
        assert result.success
    except IntentionalRandomFailure:
        pass


def test_many_events_job():
    assert many_events_job.execute_in_process().success


def test_many_events_subset_job():
    result = many_events_subset_job.execute_in_process()
    assert result.success

    executed_step_keys = [
        evt.step_key
        for evt in result.all_node_events
        if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]
    assert len(executed_step_keys) == 3


def get_sleepy():
    return sleepy_job


def test_sleepy_job():
    with instance_for_test() as instance:
        assert execute_pipeline(reconstructable(get_sleepy), instance=instance).success


def test_branch_job():
    assert branch_job.execute_in_process().success


def test_branch_job_failed():
    with pytest.raises(Exception):
        assert not branch_failed_job.execute_in_process().success


def test_spew_pipeline():
    assert log_spew_job.execute_in_process().success


def test_hammer_job():
    assert hammer_default_executor_job.execute_in_process().success


def test_resource_job_no_config():
    result = resource_job.execute_in_process()
    assert result.output_for_node("one") == 2


def test_resource_job_with_config():
    result = resource_ops.to_job(
        config={"resources": {"R1": {"config": 2}}}, resource_defs=lots_of_resources
    ).execute_in_process()
    assert result.output_for_node("one") == 3


def test_pyspark_assets_job():
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
            config=run_config, resource_defs=dir_resources
        ).execute_in_process()
        assert result.success


def test_error_monster_success():
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
        )
        .execute_in_process()
        .success
    )


def test_error_monster_success_error_on_resource():
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
        ).execute_in_process()


def test_error_monster_type_error():
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


def test_retry_job():
    assert retry_job.execute_in_process().success
