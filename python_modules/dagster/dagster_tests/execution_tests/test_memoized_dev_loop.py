import tempfile

import pytest
from dagster import (
    DagsterInvariantViolationError,
    DynamicOut,
    DynamicOutput,
    In,
    execute_pipeline,
    graph,
    op,
    reexecute_pipeline,
    resource,
    root_input_manager,
)
from dagster.core.definitions.version_strategy import VersionStrategy
from dagster.core.execution.api import create_execution_plan
from dagster.core.storage.memoizable_io_manager import versioned_filesystem_io_manager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.test_utils import instance_for_test

from .memoized_dev_loop_pipeline import asset_pipeline


def get_step_keys_to_execute(pipeline, run_config, mode, instance):
    return create_execution_plan(
        pipeline, run_config, mode, instance=instance, tags={MEMOIZED_RUN_TAG: "true"}
    ).step_keys_to_execute


def test_dev_loop_changing_versions():
    with tempfile.TemporaryDirectory() as temp_dir:

        with instance_for_test(temp_dir=temp_dir) as instance:

            run_config = {
                "solids": {
                    "create_string_1_asset": {"config": {"input_str": "apple"}},
                    "take_string_1_asset": {"config": {"input_str": "apple"}},
                },
                "resources": {"io_manager": {"config": {"base_dir": temp_dir}}},
            }

            result = execute_pipeline(
                asset_pipeline,
                run_config=run_config,
                mode="only_mode",
                tags={MEMOIZED_RUN_TAG: "true"},
                instance=instance,
            )
            assert result.success
            # Ensure that after one memoized execution, with no change to run config, that upon the next
            # computation, there are no step keys to execute.
            assert not get_step_keys_to_execute(asset_pipeline, run_config, "only_mode", instance)

            run_config["solids"]["take_string_1_asset"]["config"]["input_str"] = "banana"

            # Ensure that after changing run config that affects only the `take_string_1_asset` step, we
            # only need to execute that step.
            assert get_step_keys_to_execute(asset_pipeline, run_config, "only_mode", instance) == [
                "take_string_1_asset"
            ]
            result = reexecute_pipeline(
                asset_pipeline,
                parent_run_id=result.run_id,
                run_config=run_config,
                mode="only_mode",
                tags={MEMOIZED_RUN_TAG: "true"},
                instance=instance,
            )
            assert result.success

            # After executing with the updated run config, ensure that there are no unmemoized steps.
            assert not get_step_keys_to_execute(asset_pipeline, run_config, "only_mode", instance)

            # Ensure that the pipeline runs, but with no steps.
            result = execute_pipeline(
                asset_pipeline,
                run_config=run_config,
                mode="only_mode",
                tags={MEMOIZED_RUN_TAG: "true"},
                instance=instance,
            )
            assert result.success
            assert len(result.step_event_list) == 0


def test_memoization_with_default_strategy():
    recorder = []

    @resource()
    def my_resource():
        pass

    @op(required_resource_keys={"my_resource"})
    def my_op():
        recorder.append("entered")

    @graph
    def my_graph():
        my_op()

    class MyVersionStrategy(VersionStrategy):
        def get_solid_version(self, solid_def):
            return "foo"

        def get_resource_version(self, resource_def):
            return "foo"

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            my_job = my_graph.to_job(
                version_strategy=MyVersionStrategy(),
                resource_defs={
                    "io_manager": versioned_filesystem_io_manager.configured(
                        {"base_dir": temp_dir}
                    ),
                    "my_resource": my_resource,
                },
            )
            unmemoized_plan = create_execution_plan(my_job, instance=instance)
            assert len(unmemoized_plan.step_keys_to_execute) == 1

            result = my_job.execute_in_process()
            assert result.success
            assert len(recorder) == 1

            execution_plan = create_execution_plan(my_job, instance=instance)
            assert len(execution_plan.step_keys_to_execute) == 0

            result = my_job.execute_in_process()
            assert result.success
            assert len(recorder) == 1


def test_memoization_with_default_strategy_overriden():
    version = ["foo"]

    class MyVersionStrategy(VersionStrategy):
        def get_solid_version(self, solid_def):
            return version[0]

    recorder = []

    @op(version="override")
    def my_op():
        recorder.append("entered")

    @graph
    def my_graph():
        my_op()

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            my_job = my_graph.to_job(
                version_strategy=MyVersionStrategy(),
                resource_defs={
                    "io_manager": versioned_filesystem_io_manager.configured(
                        {"base_dir": temp_dir}
                    ),
                },
            )

            unmemoized_plan = create_execution_plan(my_job, instance=instance)
            assert len(unmemoized_plan.step_keys_to_execute) == 1

            result = my_job.execute_in_process(instance=instance)
            assert result.success

            assert len(recorder) == 1

            version.remove("foo")
            version.append("bar")

            memoized_plan = create_execution_plan(my_job, instance=instance)
            assert len(memoized_plan.step_keys_to_execute) == 0

            result = my_job.execute_in_process(instance=instance)
            assert result.success

            assert len(recorder) == 1

            # Ensure that after switching memoization tag off, that the plan recognizes every step
            # should be run.
            unmemoized_plan = create_execution_plan(
                my_job, instance=instance, tags={MEMOIZED_RUN_TAG: "false"}
            )
            assert len(unmemoized_plan.step_keys_to_execute) == 1


def test_version_strategy_root_input_manager():
    class MyVersionStrategy(VersionStrategy):
        def get_solid_version(self, _):
            return "foo"

        def get_resource_version(self, _):
            return "foo"

    @root_input_manager
    def my_input_manager(_):
        return 5

    @op(ins={"x": In(root_manager_key="my_input_manager")})
    def my_op(x):
        return x

    @graph
    def my_graph():
        my_op()

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            my_job = my_graph.to_job(
                resource_defs={
                    "io_manager": versioned_filesystem_io_manager,
                    "my_input_manager": my_input_manager,
                },
                version_strategy=MyVersionStrategy(),
            )
            result = my_job.execute_in_process(instance=instance)
            assert result.success
            post_memoization_plan = create_execution_plan(my_job, instance=instance)
            assert len(post_memoization_plan.step_keys_to_execute) == 0


def test_dynamic_memoization_error():
    class MyVersionStrategy(VersionStrategy):
        def get_solid_version(self, _):
            return "foo"

        def get_resource_version(self, _):
            return "foo"

    @op(out=DynamicOut())
    def emit():
        yield DynamicOutput(1, mapping_key="one")
        yield DynamicOutput(2, mapping_key="two")

    @op
    def return_input(x):
        return x

    @graph
    def dynamic_graph():
        x = emit().map(return_input)  # pylint: disable=no-member
        return_input(x.collect())

    @graph
    def just_mapping_graph():
        emit().map(return_input)  # pylint: disable=no-member

    with instance_for_test() as instance:
        for cur_graph in [dynamic_graph, just_mapping_graph]:
            with pytest.raises(
                DagsterInvariantViolationError,
                match="Attempted to use memoization with dynamic orchestration, which is not yet supported.",
            ):
                my_job = cur_graph.to_job(
                    version_strategy=MyVersionStrategy(),
                    resource_defs={"io_manager": versioned_filesystem_io_manager},
                )

                my_job.execute_in_process(instance=instance)
