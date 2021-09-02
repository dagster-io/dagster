from dagster.core.definitions.reconstructable import ReconstructableRepository
import pytest
from dagster import (
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterTypeCheckDidNotPass,
    execute_pipeline,
    reconstructable,
)
from dagster.core.test_utils import instance_for_test
from dagster.utils import file_relative_path
from dagster.utils.temp_file import get_temp_dir
from dagster_test.graph_job_op_toys.asset_lineage import asset_lineage_job
from dagster_test.graph_job_op_toys.composition import composition_job
from dagster_test.graph_job_op_toys.dynamic import dynamic_job
from dagster_test.graph_job_op_toys.error_monster import (
    define_errorable_resource,
    errorable_io_manager,
    error_monster,
    preset_run_config,
)
from dagster_test.graph_job_op_toys.hammer import hammer_job
from dagster_test.graph_job_op_toys.log_spew import log_spew_job
from dagster_test.graph_job_op_toys.longitudinal import (
    IntentionalRandomFailure,
    longitudinal_job,
)
from dagster_test.graph_job_op_toys.many_events import many_events_job
from dagster_test.graph_job_op_toys.pyspark_assets.pyspark_assets_job import (
    pyspark_assets_job,
    pyspark_assets_graph,
    dir_resources,
)
from dagster_test.graph_job_op_toys.repo import toys_repository
from dagster_test.graph_job_op_toys.resources import resource_graph, resource_job, lots_of_resources
from dagster_test.graph_job_op_toys.retries import retry_job
from dagster_test.graph_job_op_toys.schedules import longitudinal_schedule
from dagster_test.graph_job_op_toys.sleepy import sleepy_job
from dagster_test.graph_job_op_toys.branches import branch_job, branch_failed_job
from dagster_test.graph_job_op_toys.repo import toys_repository


def test_repo():
    assert toys_repository


def test_toys_repo():
    with instance_for_test() as instance:
        recon_repo = ReconstructableRepository.for_file(__file__, "toys_repository")
        jobs = toys_repository.get_all_pipelines()
        for job in jobs:
            recon_repo.get_reconstructable_pipeline(job.name).execute_in_process(instance=instance)


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


def get_sleepy():
    return sleepy_job


def test_sleepy_job():
    with instance_for_test() as instance:
        assert execute_pipeline(reconstructable(get_sleepy), instance=instance).success


def get_branch():
    return branch_job


def test_branch_job():
    with instance_for_test() as instance:
        assert execute_pipeline(reconstructable(get_branch), instance=instance).success


def get_branch_failed():
    return branch_failed_job


def test_branch_job_failed():
    with instance_for_test() as instance:
        assert not execute_pipeline(reconstructable(get_branch_failed), instance=instance).success


def test_spew_pipeline():
    assert log_spew_job.execute_in_process().success


def test_hammer_job():
    assert hammer_job.execute_in_process().success


def test_resource_job_no_config():
    result = resource_job.execute_in_process()
    assert result.result_for_node("one").output_values['result'] == 2


def test_resource_job_with_config():
    result = resource_graph.to_job(
        config={"resources": {"R1": {"config": 2}}}, resource_defs=lots_of_resources
    ).execute_in_process()
    assert result.result_for_node("one").output_values['result'] == 3


def test_pyspark_assets_job():
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
                            __file__, "../dagster_test/toys/pyspark_assets/asset_job_files"
                        ),
                    }
                },
                "savedir": {"config": {"dir": temp_dir}},
            },
        }

        result = pyspark_assets_graph.to_job(
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
        run_config={"solids": {"add_four": {"inputs": {"num": 3}}}},
    )

    assert result.success
    assert result.result_for_node("div_four").output_values["result"] == 7.0 / 4.0


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
