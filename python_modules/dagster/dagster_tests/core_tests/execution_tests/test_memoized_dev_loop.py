from dagster import execute_pipeline, seven
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher import DefaultRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.event_log import ConsolidatedSqliteEventLogStorage
from dagster.core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage

from .memoized_dev_loop_pipeline import basic_pipeline


def get_step_keys_to_execute(instance, pipeline, run_config, mode):
    memoized_execution_plan = instance.resolve_memoized_execution_plan(
        create_execution_plan(pipeline, run_config=run_config, mode=mode),
        run_config=run_config,
        mode=mode,
    )
    return memoized_execution_plan.step_keys_to_execute


def test_dev_loop_changing_versions():
    with seven.TemporaryDirectory() as temp_dir:
        run_store = SqliteRunStorage.from_local(temp_dir)
        event_store = ConsolidatedSqliteEventLogStorage(temp_dir)
        compute_log_manager = LocalComputeLogManager(temp_dir)
        instance = DagsterInstance(
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=run_store,
            event_storage=event_store,
            compute_log_manager=compute_log_manager,
            run_coordinator=DefaultRunCoordinator(),
            run_launcher=DefaultRunLauncher(),
        )

        run_config = {
            "solids": {
                "create_string_1": {"config": {"input_str": "apple", "base_dir": temp_dir}},
                "create_string_2": {"config": {"input_str": "apple", "base_dir": temp_dir}},
                "take_string_1": {"config": {"input_str": "apple", "base_dir": temp_dir}},
                "take_string_2": {"config": {"input_str": "apple", "base_dir": temp_dir}},
                "take_string_two_inputs": {"config": {"input_str": "apple", "base_dir": temp_dir}},
            },
            "intermediate_storage": {"filesystem": {"config": {"base_dir": temp_dir}}},
        }

        result = execute_pipeline(
            basic_pipeline,
            run_config=run_config,
            mode="only_mode",
            tags={"dagster/is_memoized_run": "true"},
            instance=instance,
        )
        assert result.success

        assert not get_step_keys_to_execute(instance, basic_pipeline, run_config, "only_mode")

        run_config["solids"]["take_string_1"]["config"]["input_str"] = "banana"

        assert set(
            get_step_keys_to_execute(instance, basic_pipeline, run_config, "only_mode")
        ) == set(["take_string_1.compute", "take_string_two_inputs.compute"])

        result2 = execute_pipeline(
            basic_pipeline,
            run_config=run_config,
            mode="only_mode",
            tags={"dagster/is_memoized_run": "true"},
            instance=instance,
        )
        assert result2.success

        assert not get_step_keys_to_execute(instance, basic_pipeline, run_config, "only_mode")

        run_config["solids"]["take_string_two_inputs"]["config"]["input_str"] = "banana"

        assert get_step_keys_to_execute(instance, basic_pipeline, run_config, "only_mode") == [
            "take_string_two_inputs.compute"
        ]

        result3 = execute_pipeline(
            basic_pipeline,
            run_config=run_config,
            mode="only_mode",
            tags={"dagster/is_memoized_run": "true"},
            instance=instance,
        )
        assert result3.success

        assert not get_step_keys_to_execute(instance, basic_pipeline, run_config, "only_mode")
