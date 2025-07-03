import os
import pickle

import dagster as dg
import dagster._check as check
import pytest
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.events import get_step_output_event
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.system_config.objects import ResolvedRunConfig


@dg.op(ins={"num": dg.In(dg.Int)}, out=dg.Out(dg.Int))
def add_one(num):
    return num + 1


@dg.op(ins={"num": dg.In(dg.Int)}, out=dg.Out(dg.Int))
def add_two(num):
    return num + 2


@dg.op(ins={"num": dg.In(dg.Int)}, out=dg.Out(dg.Int))
def add_three(num):
    return num + 3


addy_graph = dg.GraphDefinition(
    name="execution_plan_reexecution",
    node_defs=[add_one, add_two, add_three],
    dependencies={
        "add_two": {"num": dg.DependencyDefinition("add_one")},
        "add_three": {"num": dg.DependencyDefinition("add_two")},
    },
)


def define_addy_job_fs_io() -> dg.JobDefinition:
    return addy_graph.to_job()


def define_addy_job_mem_io() -> dg.JobDefinition:
    return addy_graph.to_job(
        resource_defs={"io_manager": dg.mem_io_manager}, executor_def=in_process_executor
    )


def test_execution_plan_reexecution():
    job_fn = define_addy_job_fs_io
    with dg.instance_for_test() as instance:
        run_config = {"ops": {"add_one": {"inputs": {"num": {"value": 3}}}}}
        with dg.execute_job(
            dg.reconstructable(job_fn),
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
            instance.get_run_by_id(run_id),  # pyright: ignore[reportArgumentType]
        )
        _check_known_state(known_state)

        execution_plan = create_execution_plan(
            dg.reconstructable(job_fn),
            run_config,
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
            dg.reconstructable(job_fn),
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
        with pytest.raises(dg.DagsterRunNotFoundError):
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

    with dg.instance_for_test() as instance:
        result = job_def.execute_in_process(run_config=run_config, instance=instance)
        assert result.success
        run_id = result.run_id

        ## re-execute add_two

        resolved_run_config = ResolvedRunConfig.build(job_def, run_config=run_config)
        known_state = KnownExecutionState.build_for_reexecution(
            instance,
            instance.get_run_by_id(run_id),  # pyright: ignore[reportArgumentType]
        )
        _check_known_state(known_state)

        execution_plan = create_execution_plan(
            dg.reconstructable(define_addy_job_mem_io),
            run_config,
            known_state=known_state,
        )

        dagster_run = instance.create_run_for_job(
            job_def=job_def,
            execution_plan=execution_plan,
            run_config=run_config,
            parent_run_id=run_id,
            root_run_id=run_id,
        )

        with pytest.raises(dg.DagsterInvariantViolationError):
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

    with dg.instance_for_test() as instance:
        with dg.execute_job(
            dg.reconstructable(job_fn), run_config=run_config, instance=instance
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

        with dg.execute_job(
            dg.reconstructable(job_fn),
            reexecution_options=dg.ReexecutionOptions(run_id, step_selection=["add_two"]),
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
            dg.DagsterExecutionStepNotFoundError,
            match="Step selection refers to unknown step: nope",
        ):
            dg.execute_job(
                dg.reconstructable(job_fn),
                reexecution_options=dg.ReexecutionOptions(run_id, step_selection=["nope"]),
                run_config=run_config,
                instance=instance,
            )


def define_pool_job() -> dg.JobDefinition:
    @dg.op(pool="upstream_pool")
    def upstream():
        return 1

    @dg.op(pool="downstream_pool")
    def downstream(inp):
        return inp

    @dg.job
    def pool_job():
        downstream(upstream())

    return pool_job


def test_pool_reexecution():
    with dg.instance_for_test() as instance:
        # initial execution
        with dg.execute_job(dg.reconstructable(define_pool_job), instance=instance) as result:
            parent_run = result.dagster_run
            assert parent_run.run_op_concurrency
            assert parent_run.run_op_concurrency.all_pools == {
                "upstream_pool",
                "downstream_pool",
            }
            assert parent_run.run_op_concurrency.root_key_counts == {"upstream_pool": 1}
            assert parent_run.status == DagsterRunStatus.SUCCESS

        # retry execution
        with dg.execute_job(
            dg.reconstructable(define_pool_job),
            instance=instance,
            reexecution_options=dg.ReexecutionOptions(
                parent_run_id=parent_run.run_id,
                step_selection=["downstream"],
            ),
        ) as result:
            retry_run = result.dagster_run
            assert retry_run.run_op_concurrency
            assert retry_run.run_op_concurrency.all_pools == {"downstream_pool"}
            assert retry_run.run_op_concurrency.root_key_counts == {"downstream_pool": 1}
            assert retry_run.status == DagsterRunStatus.SUCCESS
