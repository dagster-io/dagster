import os
import pickle

import dagster._check as check
import pytest
from dagster import DependencyDefinition, In, Int, Out, op
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterRunNotFoundError,
)
from dagster._core.events import get_step_output_event
from dagster._core.execution.api import ReexecutionOptions, execute_job, execute_plan
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.mem_io_manager import mem_io_manager
from dagster._core.system_config.objects import ResolvedRunConfig


@op(ins={"num": In(Int)}, out=Out(Int))
def add_one(num):
    return num + 1


@op(ins={"num": In(Int)}, out=Out(Int))
def add_two(num):
    return num + 2


@op(ins={"num": In(Int)}, out=Out(Int))
def add_three(num):
    return num + 3


addy_graph = GraphDefinition(
    name="execution_plan_reexecution",
    node_defs=[add_one, add_two, add_three],
    dependencies={
        "add_two": {"num": DependencyDefinition("add_one")},
        "add_three": {"num": DependencyDefinition("add_two")},
    },
)


def define_addy_job_fs_io() -> JobDefinition:
    return addy_graph.to_job()


def define_addy_job_mem_io() -> JobDefinition:
    return addy_graph.to_job(
        resource_defs={"io_manager": mem_io_manager}, executor_def=in_process_executor
    )


def test_execution_plan_reexecution():
    job_fn = define_addy_job_fs_io
    with instance_for_test() as instance:
        run_config = {"ops": {"add_one": {"inputs": {"num": {"value": 3}}}}}
        with execute_job(
            reconstructable(job_fn),
            run_config=run_config,
            instance=instance,
        ) as result:
            assert result.success
            run_id = result.run_id

        with open(
            os.path.join(instance.storage_directory(), run_id, "add_one", "result"),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 4

        with open(
            os.path.join(instance.storage_directory(), run_id, "add_two", "result"),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 6

        ## re-execute add_two

        resolved_run_config = ResolvedRunConfig.build(
            job_fn(),
            run_config=run_config,
        )
        known_state = KnownExecutionState.build_for_reexecution(
            instance,
            instance.get_run_by_id(run_id),
        )
        _check_known_state(known_state)

        execution_plan = ExecutionPlan.build(
            reconstructable(job_fn),
            resolved_run_config,
            known_state=known_state,
        )

        subset_plan = execution_plan.build_subset_plan(["add_two"], job_fn(), resolved_run_config)
        dagster_run = instance.create_run_for_job(
            job_def=job_fn(),
            execution_plan=subset_plan,
            run_config=run_config,
            parent_run_id=run_id,
            root_run_id=run_id,
        )

        step_events = execute_plan(
            subset_plan,
            reconstructable(job_fn),
            run_config=run_config,
            dagster_run=dagster_run,
            instance=instance,
        )
        assert not os.path.exists(
            os.path.join(instance.storage_directory(), dagster_run.run_id, "add_one", "result")
        )
        with open(
            os.path.join(instance.storage_directory(), dagster_run.run_id, "add_two", "result"),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 6

        assert not get_step_output_event(step_events, "add_one")
        assert get_step_output_event(step_events, "add_two")

        # delete ancestor run
        instance.delete_run(result.run_id)
        # ensure failure raises appropriate error
        with pytest.raises(DagsterRunNotFoundError):
            KnownExecutionState.build_for_reexecution(
                instance,
                dagster_run,
            )


def _check_known_state(known_state: KnownExecutionState):
    for step_key, outputs in known_state.dynamic_mappings.items():
        for outname, mapping_keys in outputs.items():
            check.is_list(
                mapping_keys,
                of_type=str,
                additional_message=f"Bad mapping_keys at {step_key}.{outname}",
            )


def test_execution_plan_reexecution_with_in_memory():
    job_def = define_addy_job_mem_io()
    run_config = {"ops": {"add_one": {"inputs": {"num": {"value": 3}}}}}

    with instance_for_test() as instance:
        result = job_def.execute_in_process(run_config=run_config, instance=instance)
        assert result.success
        run_id = result.run_id

        ## re-execute add_two

        resolved_run_config = ResolvedRunConfig.build(job_def, run_config=run_config)
        known_state = KnownExecutionState.build_for_reexecution(
            instance,
            instance.get_run_by_id(run_id),
        )
        _check_known_state(known_state)

        execution_plan = ExecutionPlan.build(
            reconstructable(define_addy_job_mem_io),
            resolved_run_config,
            known_state=known_state,
        )

        dagster_run = instance.create_run_for_job(
            job_def=job_def,
            execution_plan=execution_plan,
            run_config=run_config,
            parent_run_id=run_id,
            root_run_id=run_id,
        )

        with pytest.raises(DagsterInvariantViolationError):
            execute_plan(
                execution_plan.build_subset_plan(["add_two"], job_def, resolved_run_config),
                InMemoryJob(job_def),
                run_config=run_config,
                dagster_run=dagster_run,
                instance=instance,
            )


def test_job_step_key_subset_execution():
    job_fn = define_addy_job_fs_io
    run_config = {"ops": {"add_one": {"inputs": {"num": {"value": 3}}}}}

    with instance_for_test() as instance:
        with execute_job(
            reconstructable(job_fn), run_config=run_config, instance=instance
        ) as result:
            assert result.success
            run_id = result.run_id

        with open(
            os.path.join(instance.storage_directory(), run_id, "add_one", "result"),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 4

        with open(
            os.path.join(instance.storage_directory(), run_id, "add_two", "result"),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 6

        ## re-execute add_two

        with execute_job(
            reconstructable(job_fn),
            reexecution_options=ReexecutionOptions(run_id, step_selection=["add_two"]),
            run_config=run_config,
            instance=instance,
        ) as result:
            assert result.success

            step_events = result.all_node_events
            assert step_events
            assert not os.path.exists(
                os.path.join(
                    instance.storage_directory(),
                    result.run_id,
                    "add_one",
                    "result",
                )
            )
            with open(
                os.path.join(
                    instance.storage_directory(),
                    result.run_id,
                    "add_two",
                    "result",
                ),
                "rb",
            ) as read_obj:
                assert pickle.load(read_obj) == 6

            assert not get_step_output_event(step_events, "add_one")
            assert get_step_output_event(step_events, "add_two")

        with pytest.raises(
            DagsterExecutionStepNotFoundError,
            match="Step selection refers to unknown step: nope",
        ):
            execute_job(
                reconstructable(job_fn),
                reexecution_options=ReexecutionOptions(run_id, step_selection=["nope"]),
                run_config=run_config,
                instance=instance,
            )
