from collections import defaultdict

import pytest

from dagster import (
    AssetMaterialization,
    DagsterInvalidDefinitionError,
    DagsterTypeCheckDidNotPass,
    In,
    Int,
    List,
    Nothing,
    Optional,
    Out,
    Output,
    asset,
    job,
    materialize_to_memory,
    op,
)
from dagster._core.execution.api import create_execution_plan


def _define_nothing_dep_pipeline():
    @op(out={"complete": Out(Nothing)})
    def start_nothing():
        pass

    @op(
        ins={
            "add_complete": In(Nothing),
            "yield_complete": In(Nothing),
        }
    )
    def end_nothing():
        pass

    @op
    def emit_value() -> int:
        return 1

    @op(ins={"on_complete": In(Nothing), "num": In(Int)})
    def add_value(num) -> int:
        return 1 + num

    @op(
        name="yield_values",
        ins={"on_complete": In(Nothing)},
        out={
            "num_1": Out(Int),
            "num_2": Out(Int),
            "complete": Out(Nothing),
        },
    )
    def yield_values():
        yield Output(1, "num_1")
        yield Output(2, "num_2")
        yield Output(None, "complete")

    @job
    def simple_exc():
        start_complete = start_nothing()
        _, _, yield_complete = yield_values(start_complete)
        end_nothing(
            add_complete=add_value(on_complete=start_complete, num=emit_value()),
            yield_complete=yield_complete,
        )

    return simple_exc


def test_valid_nothing_dependencies():

    result = _define_nothing_dep_pipeline().execute_in_process()

    assert result.success


def test_nothing_output_something_input():
    @op(out=Out(Nothing))
    def do_nothing():
        pass

    @op(ins={"num": In(Int)})
    def add_one(num) -> int:
        return num + 1

    @job
    def bad_dep():
        add_one(do_nothing())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        bad_dep.execute_in_process()


def test_result_type_check():
    @op(out=Out(Nothing))
    def bad():
        yield Output("oops")

    @job
    def fail():
        bad()

    with pytest.raises(DagsterTypeCheckDidNotPass):
        fail.execute_in_process()


def test_nothing_inputs():
    @op(ins={"never_defined": In(Nothing)})
    def emit_one():
        return 1

    @op
    def emit_two():
        return 2

    @op
    def emit_three():
        return 3

    @op(out=Out(Nothing))
    def emit_nothing():
        pass

    @op(
        ins={
            "_one": In(Nothing),
            "one": In(Int),
            "_two": In(Nothing),
            "two": In(Int),
            "_three": In(Nothing),
            "three": In(Int),
        }
    )
    def adder(one, two, three):
        assert one == 1
        assert two == 2
        assert three == 3
        return one + two + three

    @job
    def input_test():
        _one = emit_nothing.alias("_one")()
        _two = emit_nothing.alias("_two")()
        _three = emit_nothing.alias("_three")()
        adder(
            _one=_one,
            _two=_two,
            _three=_three,
            one=emit_one(),
            two=emit_two(),
            three=emit_three(),
        )

    result = input_test.execute_in_process()
    assert result.success


def test_fanin_deps():
    called = defaultdict(int)

    @op
    def emit_two():
        return 2

    @op(out=Out(Nothing))
    def emit_nothing():
        called["emit_nothing"] += 1

    @op(
        ins={
            "ready": In(Nothing),
            "num_1": In(Int),
            "num_2": In(Int),
        }
    )
    def adder(num_1, num_2):
        assert called["emit_nothing"] == 3
        called["adder"] += 1
        return num_1 + num_2

    @job
    def input_test():
        adder(
            ready=[
                emit_nothing.alias("_one")(),
                emit_nothing.alias("_two")(),
                emit_nothing.alias("_three")(),
            ],
            num_1=emit_two.alias("emit_1")(),
            num_2=emit_two.alias("emit_2")(),
        )

    result = input_test.execute_in_process()
    assert result.success
    assert called["adder"] == 1
    assert called["emit_nothing"] == 3


def test_valid_nothing_fns():
    @op(out=Out(Nothing))
    def just_pass():
        pass

    @op(out=Out(Nothing))
    def just_pass2():
        pass

    @op(out=Out(Nothing))
    def ret_none():
        return None

    @op(out=Out(Nothing))
    def yield_none():
        yield Output(None)

    @op(out=Out(Nothing))
    def yield_stuff():
        yield AssetMaterialization.file("/path/to/nowhere")

    @job
    def fn_test():
        just_pass()
        just_pass2()
        ret_none()
        yield_none()
        yield_stuff()

    result = fn_test.execute_in_process()
    assert result.success


def test_invalid_nothing_fns():
    @op(out=Out(Nothing))
    def ret_val():
        return "val"

    @op(out=Out(Nothing))
    def yield_val():
        yield Output("val")

    with pytest.raises(DagsterTypeCheckDidNotPass):

        @job
        def fn_test():
            ret_val()

        fn_test.execute_in_process()

    with pytest.raises(DagsterTypeCheckDidNotPass):

        @job
        def fn_test2():
            yield_val()

        fn_test2.execute_in_process()


def test_wrapping_nothing():
    with pytest.raises(DagsterInvalidDefinitionError):

        @op(out=Out(List[Nothing]))
        def _():
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @op(ins={"in": In(List[Nothing])})
        def _(_in):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @op(out=Out(Optional[Nothing]))
        def _():
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @op(ins={"in": In(Optional[Nothing])})
        def _(_in):
            pass


def test_execution_plan():
    @op(out=Out(Nothing))
    def emit_nothing():
        yield AssetMaterialization.file(path="/path/")

    @op(ins={"ready": In(Nothing)})
    def consume_nothing():
        pass

    @job
    def pipe():
        consume_nothing(emit_nothing())

    plan = create_execution_plan(pipe)

    levels = plan.get_steps_to_execute_by_level()

    assert "emit_nothing" in levels[0][0].key
    assert "consume_nothing" in levels[1][0].key

    assert pipe.execute_in_process().success


def test_nothing_infer():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="which should not be included since no data will be passed for it",
    ):

        @op(ins={"_previous_steps_complete": In(Nothing)})
        def _bad(_previous_steps_complete):
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="must be used via InputDefinition and no parameter should be included in the @op decorated function",
    ):

        @op
        def _bad(_previous_steps_complete: Nothing):
            pass


def test_none_output_non_none_input():
    @op
    def op1() -> None:
        pass

    @op
    def op2(input1):
        assert input1 is None

    @job
    def job1():
        op2(op1())

    assert job1.execute_in_process().success


def test_asset_none_output_non_none_input():
    @asset
    def asset1() -> None:
        pass

    @asset
    def asset2(asset1):
        assert asset1 is None

    assert materialize_to_memory([asset1, asset2]).success


def test_asset_nothing_output_non_none_input():
    @asset(dagster_type=Nothing)
    def asset1():
        pass

    @asset
    def asset2(asset1):
        assert asset1 is None

    assert materialize_to_memory([asset1, asset2]).success
