import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DynamicOut,
    DynamicOutput,
    GraphOut,
    graph,
    job,
    op,
)


@op(out=DynamicOut())
def dynamic_numbers(_):
    yield DynamicOutput(1, mapping_key="1")
    yield DynamicOutput(2, mapping_key="2")


@op
def emit_one(_):
    return 1


@op
def echo(_, x):
    return x


@op
def add_one(_, x):
    return x + 1


def test_must_unpack():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Dynamic output must be unpacked by invoking map or collect",
    ):

        @job
        def _should_fail():
            echo(dynamic_numbers())


def test_must_unpack_composite():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Dynamic output must be unpacked by invoking map or collect",
    ):

        @graph
        def composed():
            return dynamic_numbers()

        @job
        def _should_fail():
            echo(composed())


def test_mapping():
    @job
    def mapping():
        dynamic_numbers().map(add_one).map(echo)

    result = mapping.execute_in_process()
    assert result.success


def test_mapping_multi():
    def _multi(item):
        a = add_one(item)
        b = add_one(a)
        c = add_one(b)
        return a, b, c

    @job
    def multi_map():
        a, b, c = dynamic_numbers().map(_multi)
        a.map(echo)
        b.map(echo)
        c.map(echo)

    result = multi_map.execute_in_process()
    assert result.success


def test_composite_multi_out():
    @graph(out={"one": GraphOut(), "numbers": GraphOut()})
    def multi_out():
        one = emit_one()
        numbers = dynamic_numbers()
        return {"one": one, "numbers": numbers}

    @job
    def composite_multi():
        one, numbers = multi_out()
        echo(one)
        numbers.map(echo)

    result = composite_multi.execute_in_process()
    assert result.success
