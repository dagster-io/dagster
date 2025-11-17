import tempfile

import dagster as dg
from dagster._core.definitions.executor_definition import async_executor
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import execute_job
from dagster._core.storage.fs_io_manager import fs_io_manager


def branching_job_def_async_executor() -> dg.JobDefinition:
    @dg.op(out={"a": dg.Out(is_required=False), "b": dg.Out(is_required=False)})
    async def a_or_b():
        yield dg.Output("wow", "a")

    @dg.op
    async def echo(x):
        return x

    @dg.op
    async def fail_once(context: dg.OpExecutionContext, x):
        key = context.op_handle.name
        if context.instance.run_storage.get_cursor_values({key}).get(key):
            return x
        context.instance.run_storage.set_cursor_values({key: "true"})
        raise Exception("failed (just this once)")

    @dg.job(executor_def=async_executor)
    def branching_job():
        a, b = a_or_b()
        echo(
            [
                fail_once.alias("fail_once_a")(a),
                fail_once.alias("fail_once_b")(b),
            ]
        )

    return branching_job


def can_fail_job_def_async_executor() -> dg.JobDefinition:
    @dg.op
    async def one():
        return 1

    @dg.op(config_schema={"should_fail": bool})
    async def plus_two(context, i: int) -> int:
        if context.op_config["should_fail"] is True:
            raise Exception("boom")
        return i + 2

    @dg.op
    async def plus_three(i: int) -> int:
        return i + 3

    @dg.job(executor_def=async_executor)
    def my_job():
        plus_three(plus_two(one()))

    return my_job


def fs_io_job_def_async_executor() -> dg.JobDefinition:
    @dg.op(out=dg.Out())
    async def op_a(_context):
        return [1, 2, 3]

    @dg.op
    async def op_b(_context, _df):
        return 1

    @dg.job(resource_defs={"io_manager": fs_io_manager}, executor_def=async_executor)
    def my_job():
        op_b(op_a())

    return my_job


def test_branching_reexecution_async_executor() -> None:
    with dg.instance_for_test() as instance:
        with execute_job(
            reconstructable(branching_job_def_async_executor),
            instance=instance,
        ) as result:
            assert not result.success

        with execute_job(
            reconstructable(branching_job_def_async_executor),
            instance=instance,
            reexecution_options=dg.ReexecutionOptions.from_failure(result.run_id, instance),
        ) as result_2:
            assert result_2.success
            success_steps = {ev.step_key for ev in result_2.get_step_success_events()}
            # Only the previously failing branch should be retried and succeed.
            assert "fail_once_a" in success_steps
            assert "fail_once_b" not in success_steps


def test_reexecute_subset_of_subset_async_executor() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with dg.instance_for_test() as instance:
            with execute_job(
                reconstructable(can_fail_job_def_async_executor),
                instance=instance,
                run_config={
                    "ops": {"plus_two": {"config": {"should_fail": True}}},
                    "resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}},
                },
            ) as result:
                assert not result.success

            reexecution_options = dg.ReexecutionOptions.from_failure(result.run_id, instance)
            with execute_job(
                reconstructable(can_fail_job_def_async_executor),
                instance=instance,
                run_config={
                    "ops": {"plus_two": {"config": {"should_fail": False}}},
                    "resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}},
                },
                reexecution_options=reexecution_options,
            ) as first_re_result:
                assert first_re_result.success
                assert first_re_result.output_for_node("plus_two") == 3

            with execute_job(
                reconstructable(can_fail_job_def_async_executor),
                instance=instance,
                run_config={
                    "ops": {"plus_two": {"config": {"should_fail": False}}},
                    "resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}},
                },
                reexecution_options=dg.ReexecutionOptions(
                    first_re_result.run_id,
                    step_selection=["plus_two*"],
                ),
            ) as second_re_result:
                assert second_re_result.success
                assert second_re_result.output_for_node("plus_two") == 3


def test_fs_io_manager_reexecution_async_executor() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with dg.instance_for_test() as instance:
            with execute_job(
                reconstructable(fs_io_job_def_async_executor),
                instance=instance,
                run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}}},
            ) as result:
                assert result.success

            with execute_job(
                reconstructable(fs_io_job_def_async_executor),
                instance=instance,
                run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}}},
                reexecution_options=dg.ReexecutionOptions(
                    parent_run_id=result.run_id,
                    step_selection=["op_b"],
                ),
            ) as re_result:
                assert re_result.success
                # In the core tests this is further asserted via loaded_input events;
                # here we at least assert the reexecuted subset step succeeded.
                assert {ev.step_key for ev in re_result.get_step_success_events()} == {"op_b"}
