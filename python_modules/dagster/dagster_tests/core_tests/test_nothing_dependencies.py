from collections import defaultdict

import dagster as dg
import pytest
from dagster import AssetMaterialization, Nothing
from dagster._core.execution.api import create_execution_plan


def _define_nothing_dep_job():
    @dg.op(out={"complete": dg.Out(dg.Nothing)})
    def start_nothing():
        pass

    @dg.op(
        ins={
            "add_complete": dg.In(dg.Nothing),
            "yield_complete": dg.In(dg.Nothing),
        }
    )
    def end_nothing():
        pass

    @dg.op
    def emit_value() -> int:
        return 1

    @dg.op(ins={"on_complete": dg.In(dg.Nothing), "num": dg.In(dg.Int)})
    def add_value(num) -> int:
        return 1 + num

    @dg.op(
        name="yield_values",
        ins={"on_complete": dg.In(dg.Nothing)},
        out={
            "num_1": dg.Out(dg.Int),
            "num_2": dg.Out(dg.Int),
            "complete": dg.Out(dg.Nothing),
        },
    )
    def yield_values():
        yield dg.Output(1, "num_1")
        yield dg.Output(2, "num_2")
        yield dg.Output(None, "complete")

    @dg.job
    def simple_exc():
        start_complete = start_nothing()
        _, _, yield_complete = yield_values(start_complete)
        end_nothing(
            add_complete=add_value(on_complete=start_complete, num=emit_value()),
            yield_complete=yield_complete,
        )

    return simple_exc


def test_valid_nothing_dependencies():
    result = _define_nothing_dep_job().execute_in_process()

    assert result.success


def test_output_input_type_mismatch():
    @dg.op
    def do_nothing():
        pass

    @dg.op(ins={"num": dg.In(dg.Int)})
    def add_one(num) -> int:
        return num + 1

    @dg.job
    def bad_dep():
        add_one(do_nothing())

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        bad_dep.execute_in_process()


def test_result_type_check():
    @dg.op(out=dg.Out(dg.Nothing))
    def bad():
        yield dg.Output("oops")

    @dg.job
    def fail():
        bad()

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        fail.execute_in_process()


def test_nothing_inputs():
    @dg.op(ins={"never_defined": dg.In(dg.Nothing)})
    def emit_one():
        return 1

    @dg.op
    def emit_two():
        return 2

    @dg.op
    def emit_three():
        return 3

    @dg.op(out=dg.Out(dg.Nothing))
    def emit_nothing():
        pass

    @dg.op(
        ins={
            "_one": dg.In(dg.Nothing),
            "one": dg.In(dg.Int),
            "_two": dg.In(dg.Nothing),
            "two": dg.In(dg.Int),
            "_three": dg.In(dg.Nothing),
            "three": dg.In(dg.Int),
        }
    )
    def adder(one, two, three):
        assert one == 1
        assert two == 2
        assert three == 3
        return one + two + three

    @dg.job
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

    @dg.op
    def emit_two():
        return 2

    @dg.op(out=dg.Out(dg.Nothing))
    def emit_nothing():
        called["emit_nothing"] += 1

    @dg.op(
        ins={
            "ready": dg.In(dg.Nothing),
            "num_1": dg.In(dg.Int),
            "num_2": dg.In(dg.Int),
        }
    )
    def adder(num_1, num_2):
        assert called["emit_nothing"] == 3
        called["adder"] += 1
        return num_1 + num_2

    @dg.job
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
    @dg.op(out=dg.Out(dg.Nothing))
    def just_pass():
        pass

    @dg.op(out=dg.Out(dg.Nothing))
    def just_pass2():
        pass

    @dg.op(out=dg.Out(dg.Nothing))
    def ret_none():
        return None

    @dg.op(out=dg.Out(dg.Nothing))
    def yield_none():
        yield dg.Output(None)

    @dg.op(out=dg.Out(dg.Nothing))
    def yield_stuff():
        yield AssetMaterialization.file("/path/to/nowhere")

    @dg.job
    def fn_test():
        just_pass()
        just_pass2()
        ret_none()
        yield_none()
        yield_stuff()

    result = fn_test.execute_in_process()
    assert result.success

    # test direct invocations
    just_pass()
    just_pass2()
    ret_none()
    [_ for _ in yield_none()]
    [_ for _ in yield_stuff()]


def test_invalid_nothing_fns():
    @dg.op(out=dg.Out(dg.Nothing))
    def ret_val():
        return "val"

    @dg.op(out=dg.Out(dg.Nothing))
    def yield_val():
        yield dg.Output("val")

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):

        @dg.job
        def fn_test():
            ret_val()

        fn_test.execute_in_process()

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):

        @dg.job
        def fn_test2():
            yield_val()

        fn_test2.execute_in_process()


def test_wrapping_nothing():
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.op(out=dg.Out(dg.List[dg.Nothing]))
        def _():
            pass

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.op(ins={"in": dg.In(dg.List[dg.Nothing])})
        def _(_in):
            pass

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.op(out=dg.Out(dg.Optional[dg.Nothing]))
        def _():
            pass

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.op(ins={"in": dg.In(dg.Optional[dg.Nothing])})
        def _(_in):
            pass


def test_execution_plan():
    @dg.op(out=dg.Out(dg.Nothing))
    def emit_nothing():
        yield AssetMaterialization.file(path="/path/")

    @dg.op(ins={"ready": dg.In(dg.Nothing)})
    def consume_nothing():
        pass

    @dg.job
    def pipe():
        consume_nothing(emit_nothing())

    plan = create_execution_plan(pipe)

    levels = plan.get_steps_to_execute_by_level()

    assert "emit_nothing" in levels[0][0].key
    assert "consume_nothing" in levels[1][0].key

    assert pipe.execute_in_process().success


def test_nothing_infer():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="which should not be included since no data will be passed for it",
    ):

        @dg.op(ins={"_previous_steps_complete": dg.In(dg.Nothing)})
        def _bad(_previous_steps_complete):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"must be used via In\(\) and no parameter should be included in the @op decorated"
            r" function"
        ),
    ):

        @dg.op
        def _bad(_previous_steps_complete: Nothing):  # type: ignore
            pass


def test_none_output_non_none_input():
    @dg.op
    def op1():
        pass

    @dg.op
    def op2(input1):
        assert input1 is None

    @dg.job
    def job1():
        op2(op1())

    assert job1.execute_in_process().success


def test_asset_none_output_non_none_input():
    @dg.asset
    def asset1():
        pass

    @dg.asset
    def asset2(asset1):
        assert asset1 is None

    assert dg.materialize_to_memory([asset1, asset2]).success


def test_asset_nothing_output_non_none_input():
    @dg.asset(dagster_type=Nothing)  # pyright: ignore[reportArgumentType]
    def asset1():
        pass

    @dg.asset
    def asset2(asset1):
        assert asset1 is None

    with pytest.raises(KeyError):
        assert dg.materialize_to_memory([asset1, asset2]).success
