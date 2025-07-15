import gc
from typing import NamedTuple

import dagster as dg
import objgraph
import pytest
from dagster._core.events import DagsterEventType


def test_basic():
    @dg.op(out=dg.DynamicOut())
    def should_work():
        yield dg.DynamicOutput(1, mapping_key="1")
        yield dg.DynamicOutput(2, mapping_key="2")

    assert [do.value for do in should_work()] == [1, 2]


def test_fails_without_def():
    @dg.op
    def should_fail():
        yield dg.DynamicOutput(True, mapping_key="foo")

    @dg.graph
    def wrap():
        should_fail()

    with pytest.raises(
        dg.DagsterInvariantViolationError, match="did not use DynamicOutputDefinition"
    ):
        wrap.execute_in_process(raise_on_error=True)

    # https://github.com/dagster-io/dagster/issues/9727
    # with pytest.raises(DagsterInvariantViolationError, match="did not use DynamicOutputDefinition"):
    #     list(should_fail())


def test_fails_with_wrong_output():
    @dg.op(out=dg.DynamicOut())
    def should_fail():
        yield dg.Output(1)

    @dg.graph
    def wrap():
        should_fail()

    with pytest.raises(dg.DagsterInvariantViolationError, match="must yield DynamicOutput"):
        wrap.execute_in_process(raise_on_error=True)

    # https://github.com/dagster-io/dagster/issues/9727
    # with pytest.raises(DagsterInvariantViolationError, match="must yield DynamicOutput"):
    #     list(should_fail())

    @dg.op(out=dg.DynamicOut())
    def should_also_fail():
        return 1

    @dg.graph
    def wrap_also():
        should_also_fail()

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="dynamic output 'result' expected a list of DynamicOutput objects",
    ):
        wrap_also.execute_in_process(raise_on_error=True)

    # https://github.com/dagster-io/dagster/issues/9727
    # with pytest.raises(
    #     DagsterInvariantViolationError,
    #     match="dynamic output 'result' expected a list of DynamicOutput objects",
    # ):
    #     list(should_also_fail())


def test_fails_dupe_keys():
    @dg.op(out=dg.DynamicOut())
    def should_fail():
        yield dg.DynamicOutput(True, mapping_key="dunk")
        yield dg.DynamicOutput(True, mapping_key="dunk")

    @dg.graph
    def wrap():
        should_fail()

    with pytest.raises(
        dg.DagsterInvariantViolationError, match='mapping_key "dunk" multiple times'
    ):
        wrap.execute_in_process(raise_on_error=True)

    # https://github.com/dagster-io/dagster/issues/9727
    # with pytest.raises(DagsterInvariantViolationError, match='mapping_key "dunk" multiple times'):
    #     list(should_fail())


def test_invalid_mapping_keys():
    with pytest.raises(dg.DagsterInvalidDefinitionError):
        dg.DynamicOutput(True, mapping_key="")

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        dg.DynamicOutput(True, mapping_key="?")

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        dg.DynamicOutput(True, mapping_key="foo.baz")


def test_multi_output():
    @dg.op(
        out={
            "numbers": dg.DynamicOut(int),
            "letters": dg.DynamicOut(str),
            "wildcard": dg.Out(str),
        }
    )
    def multiout():
        yield dg.DynamicOutput(1, output_name="numbers", mapping_key="1")
        yield dg.DynamicOutput(2, output_name="numbers", mapping_key="2")
        yield dg.DynamicOutput("a", output_name="letters", mapping_key="a")
        yield dg.DynamicOutput("b", output_name="letters", mapping_key="b")
        yield dg.DynamicOutput("c", output_name="letters", mapping_key="c")
        yield dg.Output("*", "wildcard")

    @dg.op
    def double(n):
        return n * 2

    @dg.job
    def multi_dyn():
        numbers, _, _ = multiout()
        numbers.map(double)

    pipe_result = multi_dyn.execute_in_process()

    assert pipe_result.success

    assert pipe_result.output_for_node("multiout", "numbers") == {"1": 1, "2": 2}
    assert pipe_result.output_for_node("multiout", "letters") == {"a": "a", "b": "b", "c": "c"}
    assert pipe_result.output_for_node("multiout", "wildcard") == "*"

    assert pipe_result.output_for_node("double") == {"1": 2, "2": 4}


def test_multi_out_map():
    @dg.op(out=dg.DynamicOut())
    def emit():
        yield dg.DynamicOutput(1, mapping_key="1")
        yield dg.DynamicOutput(2, mapping_key="2")
        yield dg.DynamicOutput(3, mapping_key="3")

    @dg.op(
        out={
            "a": dg.Out(is_required=False),
            "b": dg.Out(is_required=False),
            "c": dg.Out(is_required=False),
        },
    )
    def multiout(inp: int):
        if inp == 1:
            yield dg.Output(inp, output_name="a")
        else:
            yield dg.Output(inp, output_name="b")

    @dg.op
    def echo(a):
        return a

    @dg.job
    def destructure():
        a, b, c = emit().map(multiout)
        echo.alias("echo_a")(a.collect())
        echo.alias("echo_b")(b.collect())
        echo.alias("echo_c")(c.collect())

    result = destructure.execute_in_process()
    assert result.output_for_node("echo_a") == [1]
    assert result.output_for_node("echo_b") == [2, 3]

    # all fanned in inputs skipped -> op skips
    assert DagsterEventType.STEP_SKIPPED in [
        event.event_type for event in result.all_events if event.step_key == "echo_c"
    ]


def test_context_mapping_key():
    _observed = []

    @dg.op
    def observe_key(context, _dep=None):
        _observed.append(context.get_mapping_key())

    @dg.op(out=dg.DynamicOut())
    def emit():
        yield dg.DynamicOutput(1, mapping_key="key_1")
        yield dg.DynamicOutput(2, mapping_key="key_2")

    @dg.job
    def test():
        observe_key()
        emit().map(observe_key)

    result = test.execute_in_process()
    assert result.success
    assert _observed == [None, "key_1", "key_2"]

    # test standalone doesn't throw as well
    _observed = []
    observe_key(dg.build_op_context())
    assert _observed == [None]


def test_dynamic_with_op():
    @dg.op
    def passthrough(_ctx, _dep=None):
        pass

    @dg.op(out=dg.DynamicOut())
    def emit():
        yield dg.DynamicOutput(1, mapping_key="key_1")
        yield dg.DynamicOutput(2, mapping_key="key_2")

    @dg.graph
    def test_graph():
        emit().map(passthrough)

    assert test_graph.execute_in_process().success


class DangerNoodle(NamedTuple):
    x: int


@dg.op(out={"items": dg.DynamicOut(), "refs": dg.Out()})
def spawn():
    for i in range(10):
        yield dg.DynamicOutput(DangerNoodle(i), output_name="items", mapping_key=f"num_{i}")

    gc.collect()
    yield dg.Output(len(objgraph.by_type("DangerNoodle")), output_name="refs")


@dg.job
def no_leaks_plz():
    spawn()


@pytest.mark.parametrize("executor", ["in_process", "multiprocess"])
def test_dealloc_prev_outputs(executor):
    # Ensure dynamic outputs can be used to chunk large data objects
    # by not holding any refs to previous outputs.
    # Things that will hold on to outputs:
    # * mem io manager
    # * having hooks - they get access to output objs
    # * in process execution - output capture for execute_in_process
    with dg.instance_for_test() as inst:
        with dg.execute_job(
            dg.reconstructable(no_leaks_plz),
            instance=inst,
            run_config={"execution": {"config": {executor: {}}}},
        ) as result:
            assert result.success
            # there may be 1 still referenced by outer iteration frames
            assert result.output_for_node("spawn", "refs") <= 1


def test_collect_and_map():
    @dg.op(out=dg.DynamicOut())
    def dyn_vals():
        for i in range(3):
            yield dg.DynamicOutput(i, mapping_key=f"num_{i}")

    @dg.op
    def echo(x):
        return x

    @dg.op
    def add_each(vals, x):
        return [v + x for v in vals]

    @dg.graph
    def both_w_echo():
        d1 = dyn_vals()
        r = d1.map(lambda x: add_each(echo(d1.collect()), x))
        echo.alias("final")(r.collect())

    result = both_w_echo.execute_in_process()
    assert result.output_for_node("final") == [[0, 1, 2], [1, 2, 3], [2, 3, 4]]
