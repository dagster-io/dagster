import mock
import pytest
from dagster import (
    DagsterEvent,
    DagsterInstance,
    DagsterResourceFunctionError,
    DagsterRun,
    DagsterTypeCheckDidNotPass,
    RunStatusSensorDefinition,
    build_run_status_sensor_context,
    build_sensor_context,
    multiprocess_executor,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.events import DagsterEventType
from dagster._core.storage.fs_io_manager import fs_io_manager
from dagster._core.test_utils import ensure_dagster_tests_import, instance_for_test
from dagster._utils import file_relative_path
from dagster._utils.temp_file import get_temp_dir
from dagster_test.toys.branches import branch
from dagster_test.toys.composition import composition_job
from dagster_test.toys.dynamic import dynamic
from dagster_test.toys.error_monster import (
    define_errorable_resource,
    error_monster,
    errorable_io_manager,
)
from dagster_test.toys.hammer import hammer
from dagster_test.toys.log_spew import log_spew
from dagster_test.toys.longitudinal import IntentionalRandomFailure, longitudinal
from dagster_test.toys.many_events import many_events
from dagster_test.toys.pyspark_assets.pyspark_assets_job import dir_resources, pyspark_assets
from dagster_test.toys.repo import toys_repository
from dagster_test.toys.resources import lots_of_resources, resource_ops
from dagster_test.toys.retries import retry
from dagster_test.toys.schedules import longitudinal_schedule
from dagster_test.toys.sensors import get_toys_sensors
from dagster_test.toys.sleepy import sleepy
from dagster_test.toys.software_defined_assets import software_defined_assets

ensure_dagster_tests_import()
from dagster_tests.execution_tests.engine_tests.test_step_delegating_executor import (
    test_step_delegating_executor,
)
from slack_sdk.web.client import WebClient


@pytest.fixture(name="instance")
def instance():
    with instance_for_test() as instance:
        yield instance


@pytest.mark.parametrize(
    "sensor",
    [sensor_def for sensor_def in get_toys_sensors()],
    ids=[sensor_def.name for sensor_def in get_toys_sensors()],
)
@mock.patch.object(WebClient, "chat_postMessage", return_value=None)
def test_sensor(_mock_method, instance: DagsterInstance, sensor: SensorDefinition) -> None:
    sensor(
        build_run_status_sensor_context(
            sensor_name=sensor.name,
            dagster_event=mock.MagicMock(spec=DagsterEvent),
            dagster_instance=instance,
            dagster_run=mock.MagicMock(spec=DagsterRun),
        )
        if isinstance(sensor, RunStatusSensorDefinition)
        else build_sensor_context()
    )


@pytest.fixture(name="executor_def", params=[multiprocess_executor, test_step_delegating_executor])
def executor_def_fixture(request):
    return request.param


def test_repo():
    assert toys_repository


def test_dynamic_job(executor_def):
    assert dynamic.to_job(executor_def=executor_def).execute_in_process().success


def test_longitudinal_job(executor_def):
    partitions_def = longitudinal_schedule().job.partitions_def
    try:
        result = longitudinal.to_job(
            resource_defs={"io_manager": fs_io_manager},
            executor_def=executor_def,
            config=longitudinal_schedule().job.partitioned_config,
        ).execute_in_process(partition_key=partitions_def.get_partition_keys()[0])
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


def test_spew_job(executor_def):
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
            "ops": {
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
                            "../dagster_test/toys/pyspark_assets/asset_job_files",
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
        run_config={"ops": {"add_four": {"inputs": {"num": {"value": 3}}}}},
    )

    assert result.success
    assert result.output_for_node("div_four") == 7.0 / 4.0


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
    assert (
        Definitions(
            assets=software_defined_assets,
            jobs=[define_asset_job("all_assets")],
        )
        .get_job_def("all_assets")
        .execute_in_process()
        .success
    )
