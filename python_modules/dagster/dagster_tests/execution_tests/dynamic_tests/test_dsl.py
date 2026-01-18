import dagster as dg
import pytest


@dg.op(out=dg.DynamicOut())
def dynamic_numbers(_):
    yield dg.DynamicOutput(1, mapping_key="1")
    yield dg.DynamicOutput(2, mapping_key="2")


@dg.op
def emit_one(_):
    return 1


@dg.op
def echo(_, x):
    return x


@dg.op
def add_one(_, x):
    return x + 1


def test_must_unpack():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Dynamic output must be unpacked by invoking map or collect",
    ):

        @dg.job
        def _should_fail():
            echo(dynamic_numbers())


def test_must_unpack_composite():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Dynamic output must be unpacked by invoking map or collect",
    ):

        @dg.graph
        def composed():
            return dynamic_numbers()

        @dg.job
        def _should_fail():
            echo(composed())


def test_mapping():
    @dg.job
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

    @dg.job
    def multi_map():
        a, b, c = dynamic_numbers().map(_multi)
        a.map(echo)
        b.map(echo)
        c.map(echo)

    result = multi_map.execute_in_process()
    assert result.success


def test_composite_multi_out():
    @dg.graph(out={"one": dg.GraphOut(), "numbers": dg.GraphOut()})
    def multi_out():
        one = emit_one()
        numbers = dynamic_numbers()
        return {"one": one, "numbers": numbers}

    @dg.job
    def composite_multi():
        one, numbers = multi_out()  # pyright: ignore[reportGeneralTypeIssues]
        echo(one)
        numbers.map(echo)

    result = composite_multi.execute_in_process()
    assert result.success
