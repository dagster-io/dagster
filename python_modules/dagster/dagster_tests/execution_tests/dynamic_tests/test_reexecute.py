from typing import List

import pytest
from dagster import (
    AssetSelection,
    DynamicOutput,
    OpExecutionContext,
    ReexecutionOptions,
    define_asset_job,
    execute_job,
    fs_io_manager,
    graph_asset,
    in_process_executor,
    job,
    op,
    reconstructable,
)
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.events import Output
from dagster._core.definitions.output import DynamicOut, Out
from dagster._core.errors import DagsterExecutionStepNotFoundError
from dagster._core.test_utils import instance_for_test


@op
def multiply_by_two(context, y):
    context.log.info("multiply_by_two is returning " + str(y * 2))
    return y * 2


@op
def multiply_inputs(context, y, ten):
    # current_run = context.instance.get_run_by_id(context.run_id)
    # if y == 2 and current_run.parent_run_id is None:
    #     raise Exception()
    context.log.info("multiply_inputs is returning " + str(y * ten))
    return y * ten


@op
def emit_ten(_):
    return 10


@op(out=DynamicOut())
def emit(_):
    for i in range(3):
        yield DynamicOutput(value=i, mapping_key=str(i))


@job(executor_def=in_process_executor)
def dynamic_job():
    emit().map(lambda n: multiply_by_two(multiply_inputs(n, emit_ten())))


def test_map():
    result = dynamic_job.execute_in_process()
    assert result.success


def test_reexec_from_parent_basic():
    with instance_for_test() as instance:
        parent_result = execute_job(
            reconstructable(dynamic_job),
            instance=instance,
        )
        parent_run_id = parent_result.run_id

        with execute_job(
            reconstructable(dynamic_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["emit"],
            ),
        ) as reexec_result:
            assert reexec_result.success
            assert reexec_result.output_for_node("emit") == {
                "0": 0,
                "1": 1,
                "2": 2,
            }


def test_reexec_from_parent_1():
    with instance_for_test() as instance:
        parent_result = execute_job(reconstructable(dynamic_job), instance=instance)
        parent_run_id = parent_result.run_id

        with execute_job(
            reconstructable(dynamic_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["multiply_inputs[0]"],
            ),
        ) as reexec_result:
            assert reexec_result.success
            assert reexec_result.output_for_node("multiply_inputs") == {
                "0": 0,
            }


def test_reexec_from_parent_dynamic():
    with instance_for_test() as instance:
        parent_result = execute_job(reconstructable(dynamic_job), instance=instance)
        parent_run_id = parent_result.run_id
        with execute_job(
            reconstructable(dynamic_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["multiply_inputs[?]"],
            ),
        ) as result:
            assert result.success
            assert result.output_for_node("multiply_inputs") == {"0": 0, "1": 10, "2": 20}


def test_reexec_from_parent_2():
    with instance_for_test() as instance:
        parent_result = execute_job(reconstructable(dynamic_job), instance=instance)
        parent_run_id = parent_result.run_id

        with execute_job(
            reconstructable(dynamic_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["multiply_by_two[1]"],
            ),
        ) as reexec_result:
            assert reexec_result.success
            assert reexec_result.output_for_node("multiply_by_two") == {
                "1": 20,
            }


def test_reexec_from_parent_3():
    with instance_for_test() as instance:
        parent_result = execute_job(reconstructable(dynamic_job), instance=instance)
        parent_run_id = parent_result.run_id

        with execute_job(
            reconstructable(dynamic_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["multiply_inputs[1]", "multiply_by_two[2]"],
            ),
        ) as reexec_result:
            assert reexec_result.success
            assert reexec_result.output_for_node("multiply_inputs") == {
                "1": 10,
            }
            assert reexec_result.output_for_node("multiply_by_two") == {
                "2": 40,
            }


@op
def echo(x):
    return x


@op
def adder(ls: List[int]) -> int:
    return sum(ls)


@op(out=DynamicOut())
def dynamic_op():
    for i in range(10):
        yield DynamicOutput(value=i, mapping_key=str(i))


def dynamic_with_optional_output_job():
    @op(out=DynamicOut(is_required=False))
    def dynamic_optional_output_op(context):
        for i in range(10):
            if (
                # re-execution run skipped odd numbers
                context.run.parent_run_id
                and i % 2 == 0
            ) or (
                # root run skipped even numbers
                not context.run.parent_run_id
                and i % 2 == 1
            ):
                yield DynamicOutput(value=i, mapping_key=str(i))

    @job(resource_defs={"io_manager": fs_io_manager})
    def _dynamic_with_optional_output_job():
        dynamic_results = dynamic_optional_output_op().map(echo)
        adder(dynamic_results.collect())

    return _dynamic_with_optional_output_job


def test_reexec_dynamic_with_optional_output_job_1():
    with instance_for_test() as instance:
        result = dynamic_with_optional_output_job().execute_in_process(instance=instance)

        # re-execute all
        with execute_job(
            reconstructable(dynamic_with_optional_output_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
            ),
        ) as re_result:
            assert re_result.success
            assert re_result.output_for_node("adder") == sum([i for i in range(10) if i % 2 == 0])


def test_reexec_dynamic_with_optional_output_job_2():
    with instance_for_test() as instance:
        result = dynamic_with_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source yielded an output
        with execute_job(
            reconstructable(dynamic_with_optional_output_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
                step_selection=["echo[1]"],
            ),
        ) as re_result:
            assert re_result.success
            assert re_result.output_for_node("echo") == {
                "1": 1,
            }


def test_reexec_dynamic_with_optional_output_job_3():
    with instance_for_test() as instance:
        result = dynamic_with_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source did not yield
        # -> error because the dynamic step wont exist in execution plan
        with pytest.raises(
            DagsterExecutionStepNotFoundError,
            match=r"Step selection refers to unknown step: echo\[0\]",
        ):
            execute_job(
                reconstructable(dynamic_with_optional_output_job),
                instance=instance,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=result.run_id,
                    step_selection=["echo[0]"],
                ),
            )


def dynamic_with_transitive_optional_output_job():
    @op(out=Out(is_required=False))
    def add_one_with_optional_output(context, i: int):
        if (
            context.run.parent_run_id
            and i % 2 == 0  # re-execution run skipped odd numbers
            or not context.run.parent_run_id
            and i % 2 == 1  # root run skipped even numbers
        ):
            yield Output(i + 1)

    @job(resource_defs={"io_manager": fs_io_manager})
    def _dynamic_with_transitive_optional_output_job():
        dynamic_results = dynamic_op().map(lambda n: echo(add_one_with_optional_output(n)))
        adder(dynamic_results.collect())

    return _dynamic_with_transitive_optional_output_job


def test_reexec_dynamic_with_transitive_optional_output_job_1():
    with instance_for_test() as instance:
        result = dynamic_with_transitive_optional_output_job().execute_in_process(instance=instance)
        assert result.success
        assert result.output_for_node("adder") == sum([i + 1 for i in range(10) if i % 2 == 1])

        # re-execute all
        with execute_job(
            reconstructable(dynamic_with_transitive_optional_output_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
            ),
        ) as re_result:
            assert re_result.success
            assert re_result.output_for_node("adder") == sum(
                [i + 1 for i in range(10) if i % 2 == 0]
            )


def test_reexec_dynamic_with_transitive_optional_output_job_2():
    with instance_for_test() as instance:
        result = dynamic_with_transitive_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source yielded an output
        with execute_job(
            reconstructable(dynamic_with_transitive_optional_output_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
                step_selection=["echo[1]"],
            ),
        ) as re_result:
            assert re_result.success
            assert re_result.output_for_node("echo") == {"1": 2}


def test_reexec_dynamic_with_transitive_optional_output_job_3():
    with instance_for_test() as instance:
        result = dynamic_with_transitive_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source did not yield
        re_result = execute_job(
            reconstructable(dynamic_with_transitive_optional_output_job),
            instance=instance,
            raise_on_error=False,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
                step_selection=["echo[0]"],
            ),
        )
        # when all the previous runs have skipped yielding the source,
        # run would fail because of run_id returns None
        # FIXME: https://github.com/dagster-io/dagster/issues/3511
        # ideally it should skip the step because all its previous runs have skipped and finish the run successfully
        assert not re_result.success


def test_reexec_all_steps_issue():
    with instance_for_test() as instance:
        result_1 = dynamic_job.execute_in_process(instance=instance)
        assert result_1.success

        result_2 = execute_job(
            reconstructable(dynamic_job),
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
                step_selection=["+multiply_inputs[?]"],
            ),
            instance=instance,
        )
        assert result_2.success


@op(
    out={
        "some": Out(is_required=False),
        "none": Out(is_required=False),
        "skip": Out(is_required=False),
    }
)
def some_none_skip():
    yield Output("abc", "some")
    yield Output("", "none")


@op
def fail_once(context: OpExecutionContext, x):
    key = context.op_handle.name
    map_key = context.get_mapping_key()
    if map_key:
        key += f"[{map_key}]"
    if context.instance.run_storage.get_cursor_values({key}).get(key):
        return x
    context.instance.run_storage.set_cursor_values({key: "true"})
    raise Exception("failed (just this once)")


@op(out=DynamicOut())
def fan_out(y: str):
    for letter in y:
        yield DynamicOutput(letter, mapping_key=letter)


@job(executor_def=in_process_executor)
def fail_job():
    some, _n, _s = some_none_skip()
    fan_out(some).map(fail_once).map(echo)


def test_resume_failed_mapped():
    with instance_for_test() as instance:
        result = execute_job(reconstructable(fail_job), instance)
        assert not result.success
        success_steps = {ev.step_key for ev in result.get_step_success_events()}
        assert success_steps == {"some_none_skip", "fan_out"}

        result_2 = execute_job(
            reconstructable(fail_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result.run_id, instance),
        )
        assert result_2.success
        success_steps = {ev.step_key for ev in result_2.get_step_success_events()}
        assert success_steps == {
            "fail_once[a]",
            "fail_once[b]",
            "fail_once[c]",
            "echo[a]",
            "echo[b]",
            "echo[c]",
        }


def _branching_graph():
    some, none, skip = some_none_skip()
    dyn_some = fan_out.alias("fan_out_some")(fail_once.alias("fail_once_some")(some))
    dyn_none = fan_out.alias("fan_out_none")(fail_once.alias("fail_once_none")(none))
    dyn_skip = fan_out.alias("fan_out_skip")(fail_once.alias("fail_once_skip")(skip))
    col_some = echo.alias("echo_some")(
        dyn_some.map(fail_once.alias("fail_once_fan_some")).collect()
    )
    col_none = echo.alias("echo_none")(
        dyn_none.map(fail_once.alias("fail_once_fan_none")).collect()
    )
    col_skip = echo.alias("echo_skip")(
        dyn_skip.map(fail_once.alias("fail_once_fan_skip")).collect()
    )
    return echo.alias("final")([col_some, col_none, col_skip])


@job(executor_def=in_process_executor)
def branching_job():
    _branching_graph()


def test_branching():
    with instance_for_test() as instance:
        result = execute_job(reconstructable(branching_job), instance)
        assert not result.success
        success_steps = {ev.step_key for ev in result.get_step_success_events()}
        assert success_steps == {"some_none_skip"}
        assert {ev.step_key for ev in result.get_step_skipped_events()} == {
            "fan_out_skip",
            "fail_once_skip",
            "echo_skip",
        }

        result_2 = execute_job(
            reconstructable(branching_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result.run_id, instance),
        )
        success_steps = {ev.step_key for ev in result_2.get_step_success_events()}
        assert success_steps == {
            "fan_out_some",
            "fail_once_some",
            "fan_out_none",
            "fail_once_none",
            "echo_none",
        }

        result_3 = execute_job(
            reconstructable(branching_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result_2.run_id, instance),
        )
        success_steps = {ev.step_key for ev in result_3.get_step_success_events()}
        assert success_steps == {
            "fail_once_fan_some[a]",
            "fail_once_fan_some[b]",
            "fail_once_fan_some[c]",
            "echo_some",
            "final",
        }
        with result_3:
            assert result_3.output_for_node("echo_some") == ["a", "b", "c"]
            # some, none, skip (absent)
            assert result_3.output_for_node("final") == [["a", "b", "c"], []]


@op(out=DynamicOut())
def emit_nums():
    for i in range(4):
        yield DynamicOutput(i, mapping_key=str(i))


@op
def fail_n(context: OpExecutionContext, x):
    map_key = context.get_mapping_key()
    assert map_key
    key = f"{context.op_handle.name}[{map_key}]"

    fails = int(context.instance.run_storage.get_cursor_values({key}).get(key, "0"))
    if fails >= int(map_key):
        return x
    fails += 1
    context.instance.run_storage.set_cursor_values({key: str(fails)})
    raise Exception(f"failed {fails} out of {map_key}")


def _mapped_fail_graph():
    return echo(emit_nums().map(fail_n).collect())


@job(executor_def=in_process_executor)
def mapped_fail_job():
    _mapped_fail_graph()


def test_many_retries():
    with instance_for_test() as instance:
        result = execute_job(reconstructable(mapped_fail_job), instance)
        assert not result.success
        success_steps = {ev.step_key for ev in result.get_step_success_events()}
        assert success_steps == {"emit_nums", "fail_n[0]"}

        result_2 = execute_job(
            reconstructable(mapped_fail_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result.run_id, instance),
        )
        assert not result.success
        success_steps = {ev.step_key for ev in result_2.get_step_success_events()}
        assert success_steps == {"fail_n[1]"}

        result_3 = execute_job(
            reconstructable(mapped_fail_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result_2.run_id, instance),
        )
        assert not result.success
        success_steps = {ev.step_key for ev in result_3.get_step_success_events()}
        assert success_steps == {"fail_n[2]"}

        result_4 = execute_job(
            reconstructable(mapped_fail_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result_3.run_id, instance),
        )
        assert result_4.success
        success_steps = {ev.step_key for ev in result_4.get_step_success_events()}
        assert success_steps == {"fail_n[3]", "echo"}


@graph_asset
def branching_asset():
    return _branching_graph()


@asset
def echo_branching(branching_asset):
    return branching_asset


@asset
def absent_asset(branching_asset):
    return branching_asset


@graph_asset
def mapped_fail_asset():
    return _mapped_fail_graph()


@asset
def echo_mapped(mapped_fail_asset):
    return mapped_fail_asset


def asset_job():
    return define_asset_job(
        "asset_job",
        selection=AssetSelection.assets(
            branching_asset,
            echo_branching,
            mapped_fail_asset,
            echo_mapped,
        ),
        executor_def=in_process_executor,
    ).resolve(
        assets=[
            branching_asset,
            echo_branching,
            absent_asset,
            mapped_fail_asset,
            echo_mapped,
        ],
        source_assets=[],
    )


def test_assets():
    # ensure complex re-execution behavior works when assets & graphs are layered atop

    with instance_for_test() as instance:
        result = execute_job(reconstructable(asset_job), instance)
        assert not result.success
        success_steps = {ev.step_key for ev in result.get_step_success_events()}
        assert success_steps == {
            "branching_asset.some_none_skip",
            "mapped_fail_asset.emit_nums",
            "mapped_fail_asset.fail_n[0]",
        }
        assert {ev.step_key for ev in result.get_step_skipped_events()} == {
            "branching_asset.fan_out_skip",
            "branching_asset.fail_once_skip",
            "branching_asset.echo_skip",
        }

        result_2 = execute_job(
            reconstructable(asset_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result.run_id, instance),
        )
        success_steps = {ev.step_key for ev in result_2.get_step_success_events()}
        assert success_steps == {
            "branching_asset.fan_out_some",
            "branching_asset.fail_once_some",
            "branching_asset.fan_out_none",
            "branching_asset.fail_once_none",
            "branching_asset.echo_none",
            "mapped_fail_asset.fail_n[1]",
        }

        result_3 = execute_job(
            reconstructable(asset_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result_2.run_id, instance),
        )
        success_steps = {ev.step_key for ev in result_3.get_step_success_events()}
        assert success_steps == {
            "branching_asset.fail_once_fan_some[a]",
            "branching_asset.fail_once_fan_some[b]",
            "branching_asset.fail_once_fan_some[c]",
            "branching_asset.echo_some",
            "branching_asset.final",
            "echo_branching",
            "mapped_fail_asset.fail_n[2]",
        }

        result_4 = execute_job(
            reconstructable(asset_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result_3.run_id, instance),
        )
        success_steps = {ev.step_key for ev in result_4.get_step_success_events()}
        assert success_steps == {
            "mapped_fail_asset.fail_n[3]",
            "mapped_fail_asset.echo",
            "echo_mapped",
        }
