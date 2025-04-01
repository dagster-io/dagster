import pytest
from dagster import DagsterInvalidDefinitionError, DynamicOut, DynamicOutput, graph, job, op


@op(out=DynamicOut())
def dynamic_op():
    yield DynamicOutput(1, mapping_key="1")
    yield DynamicOutput(2, mapping_key="2")


@op(out=DynamicOut())
def dynamic_echo(x):
    yield DynamicOutput(x, mapping_key="echo")


@op
def echo(x):
    return x


@op
def add(x, y):
    return x + y


def test_fan_in():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Problematic dependency on dynamic output "dynamic_op:result"',
    ):

        @job
        def _should_fail():
            numbers = []
            dynamic_op().map(numbers.append)
            echo(numbers)


def test_multi_direct():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @job
        def _should_fail():
            def _add(x):
                dynamic_op().map(lambda y: add(x, y))

            dynamic_op().map(_add)


def test_multi_indirect():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @job
        def _should_fail():
            def _add(x):
                dynamic_op().map(lambda y: add(x, y))

            dynamic_op().map(lambda z: _add(echo(z)))


def test_multi_composite_out():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @graph
        def composed_echo():
            return dynamic_op().map(echo)

        @job
        def _should_fail():
            def _complex(item):
                composed_echo().map(lambda y: add(y, item))  # pyright: ignore[reportAttributeAccessIssue]

            dynamic_op().map(_complex)


def test_multi_composite_in():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            'cannot be downstream of dynamic output "dynamic_op:result" since input "a" maps to'
            " a node that is already downstream of another dynamic output"
        ),
    ):

        @graph
        def composed_add(a):
            dynamic_op().map(lambda b: add(a, b))

        @job
        def _should_fail():
            dynamic_op().map(lambda x: composed_add(echo(x)))


def test_multi_composite_in_2():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            'cannot be downstream of dynamic output "dynamic_op:result" since input "a" maps to'
            " a node that is already downstream of another dynamic output"
        ),
    ):

        @graph
        def composed_add(a):
            dynamic_op().map(lambda b: add(a, b))

        @graph
        def indirect(a):
            composed_add(a)

        @job
        def _should_fail():
            dynamic_op().map(lambda x: indirect(echo(x)))


def test_multi_composite_in_3():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            'cannot be downstream of dynamic output "dynamic_op:result" since input "a" maps to'
            " a node that is already downstream of another dynamic output"
        ),
    ):

        @graph
        def composed(a):
            dynamic_echo(a).map(echo)

        @job
        def _should_fail():
            dynamic_op().map(composed)


def test_multi_composite_in_4():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            'cannot be downstream of dynamic output "dynamic_op:result" since input "a" maps to'
            " a node that is already downstream of another dynamic output"
        ),
    ):

        @graph
        def composed(a):
            dynamic_echo(a).map(echo)

        @graph
        def indirect(a):
            composed(a)

        @job
        def _should_fail():
            dynamic_op().map(indirect)


def test_direct_dep():
    @op(out=DynamicOut())
    def dynamic_add(_, x):
        yield DynamicOutput(x + 1, mapping_key="1")
        yield DynamicOutput(x + 2, mapping_key="2")

    @job
    def _is_fine_1():
        def _add(item):
            dynamic_add(item)

        dynamic_op().map(_add)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @job
        def _should_fail():
            def _add_echo(item):
                dynamic_add(item).map(echo)

            dynamic_op().map(_add_echo)

    @job
    def _is_fine_2():
        dynamic_op().map(dynamic_add)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @job
        def _should_fail():
            echo(dynamic_op().map(dynamic_add).collect())


def test_collect_and_dep():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot both collect over dynamic output",
    ):

        @job
        def _bad():
            x = dynamic_op()
            x.map(lambda y: add(y, x.collect()))

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be both downstream of dynamic output",
    ):

        @job
        def _bad_other():
            x = dynamic_op()
            x.map(lambda y: add(x.collect(), y))
