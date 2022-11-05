import gc
from typing import NamedTuple

import objgraph
import pytest

from dagster import (
    DynamicOut,
    DynamicOutput,
    Out,
    build_op_context,
    execute_job,
    graph,
    job,
    op,
    reconstructable,
)
from dagster._core.definitions.events import Output
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.events import DagsterEventType
from dagster._core.test_utils import instance_for_test


def test_basic():
    @op(out=DynamicOut())
    def should_work():
        yield DynamicOutput(1, mapping_key="1")
        yield DynamicOutput(2, mapping_key="2")

    assert [do.value for do in should_work()] == [1, 2]


def test_fails_without_def():
    @op
    def should_fail():
        yield DynamicOutput(True, mapping_key="foo")

    @graph
    def wrap():
        should_fail()

    with pytest.raises(DagsterInvariantViolationError, match="did not use DynamicOutputDefinition"):
        wrap.execute_in_process(raise_on_error=True)

    # https://github.com/dagster-io/dagster/issues/9727
    # with pytest.raises(DagsterInvariantViolationError, match="did not use DynamicOutputDefinition"):
    #     list(should_fail())


def test_fails_with_wrong_output():
    @op(out=DynamicOut())
    def should_fail():
        yield Output(1)

    @graph
    def wrap():
        should_fail()

    with pytest.raises(DagsterInvariantViolationError, match="must yield DynamicOutput"):
        wrap.execute_in_process(raise_on_error=True)

    # https://github.com/dagster-io/dagster/issues/9727
    # with pytest.raises(DagsterInvariantViolationError, match="must yield DynamicOutput"):
    #     list(should_fail())

    @op(out=DynamicOut())
    def should_also_fail():
        return 1

    @graph
    def wrap_also():
        should_also_fail()

    with pytest.raises(
        DagsterInvariantViolationError,
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
    @op(out=DynamicOut())
    def should_fail():
        yield DynamicOutput(True, mapping_key="dunk")
        yield DynamicOutput(True, mapping_key="dunk")

    @graph
    def wrap():
        should_fail()

    with pytest.raises(DagsterInvariantViolationError, match='mapping_key "dunk" multiple times'):
        wrap.execute_in_process(raise_on_error=True)

    # https://github.com/dagster-io/dagster/issues/9727
    # with pytest.raises(DagsterInvariantViolationError, match='mapping_key "dunk" multiple times'):
    #     list(should_fail())


def test_invalid_mapping_keys():
    with pytest.raises(DagsterInvalidDefinitionError):
        DynamicOutput(True, mapping_key="")

    with pytest.raises(DagsterInvalidDefinitionError):
        DynamicOutput(True, mapping_key="?")

    with pytest.raises(DagsterInvalidDefinitionError):
        DynamicOutput(True, mapping_key="foo.baz")


def test_multi_output():
    @op(
        out={
            "numbers": DynamicOut(int),
            "letters": DynamicOut(str),
            "wildcard": Out(str),
        }
    )
    def multiout():
        yield DynamicOutput(1, output_name="numbers", mapping_key="1")
        yield DynamicOutput(2, output_name="numbers", mapping_key="2")
        yield DynamicOutput("a", output_name="letters", mapping_key="a")
        yield DynamicOutput("b", output_name="letters", mapping_key="b")
        yield DynamicOutput("c", output_name="letters", mapping_key="c")
        yield Output("*", "wildcard")

    @op
    def double(n):
        return n * 2

    @job
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
    @op(out=DynamicOut())
    def emit():
        yield DynamicOutput(1, mapping_key="1")
        yield DynamicOutput(2, mapping_key="2")
        yield DynamicOutput(3, mapping_key="3")

    @op(
        out={
            "a": Out(is_required=False),
            "b": Out(is_required=False),
            "c": Out(is_required=False),
        },
    )
    def multiout(inp: int):
        if inp == 1:
            yield Output(inp, output_name="a")
        else:
            yield Output(inp, output_name="b")

    @op
    def echo(a):
        return a

    @job
    def destructure():
        a, b, c = emit().map(multiout)
        echo.alias("echo_a")(a.collect())
        echo.alias("echo_b")(b.collect())
        echo.alias("echo_c")(c.collect())

    result = destructure.execute_in_process()
    assert result.output_for_node("echo_a") == [1]
    assert result.output_for_node("echo_b") == [2, 3]

    # all fanned in inputs skipped -> solid skips
    assert DagsterEventType.STEP_SKIPPED in [
        event.event_type for event in result.all_events if event.step_key == "echo_c"
    ]


def test_context_mapping_key():
    _observed = []

    @op
    def observe_key(context, _dep=None):
        _observed.append(context.get_mapping_key())

    @op(out=DynamicOut())
    def emit():
        yield DynamicOutput(1, mapping_key="key_1")
        yield DynamicOutput(2, mapping_key="key_2")

    @job
    def test():
        observe_key()
        emit().map(observe_key)

    result = test.execute_in_process()
    assert result.success
    assert _observed == [None, "key_1", "key_2"]

    # test standalone doesn't throw as well
    _observed = []
    observe_key(build_op_context())
    assert _observed == [None]


def test_dynamic_with_op():
    @op
    def passthrough(_ctx, _dep=None):
        pass

    @op(out=DynamicOut())
    def emit():
        yield DynamicOutput(1, mapping_key="key_1")
        yield DynamicOutput(2, mapping_key="key_2")

    @graph
    def test_graph():
        emit().map(passthrough)

    assert test_graph.execute_in_process().success


class DangerNoodle(NamedTuple):
    x: int


@op(out={"items": DynamicOut(), "refs": Out()})
def spawn():
    for i in range(10):
        yield DynamicOutput(DangerNoodle(i), output_name="items", mapping_key=f"num_{i}")

    gc.collect()
    yield Output(len(objgraph.by_type("DangerNoodle")), output_name="refs")


@job
def no_leaks_plz():
    spawn()


def test_dealloc_prev_outputs():
    # Ensure dynamic outputs can be used to chunk large data objects
    # by not holding any refs to previous outputs.
    # Things that will hold on to outputs:
    # * mem io manager
    # * having hooks - they get access to output objs
    # * in process execution - output capture for execute_in_process
    with instance_for_test() as inst:
        with execute_job(
            reconstructable(no_leaks_plz),
            instance=inst,
        ) as result:
            assert result.success
            # there may be 1 still referenced by outer iteration frames
            assert result.output_for_node("spawn", "refs") <= 1


def test_collect_and_map():
    @op(out=DynamicOut())
    def dyn_vals():
        for i in range(3):
            yield DynamicOutput(i, mapping_key=f"num_{i}")

    @op
    def echo(x):
        return x

    @op
    def add_each(vals, x):
        return [v + x for v in vals]

    @graph
    def both_w_echo():
        d1 = dyn_vals()
        r = d1.map(lambda x: add_each(echo(d1.collect()), x))
        echo.alias("final")(r.collect())

    result = both_w_echo.execute_in_process()
    assert result.output_for_node("final") == [[0, 1, 2], [1, 2, 3], [2, 3, 4]]
