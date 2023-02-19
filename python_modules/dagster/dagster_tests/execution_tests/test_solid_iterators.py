from dagster import AssetMaterialization, Output
from dagster._annotations import experimental
from dagster._core.definitions.decorators import op
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_generator_return_solid():
    def _gen():
        yield Output("done")

    @op
    def gen_ret_solid(_):
        return _gen()

    result = wrap_op_in_graph_and_execute(gen_ret_solid)
    assert result.output_value() == "done"


def test_generator_yield_solid():
    def _gen():
        yield Output("done")

    @op
    def gen_yield_solid(_):
        for event in _gen():
            yield event

    result = wrap_op_in_graph_and_execute(gen_yield_solid)
    assert result.output_value() == "done"


def test_generator_yield_from_solid():
    def _gen():
        yield Output("done")

    @op
    def gen_yield_solid(_):
        yield from _gen()

    result = wrap_op_in_graph_and_execute(gen_yield_solid)
    assert result.output_value() == "done"


def test_nested_generator_solid():
    def _gen1():
        yield AssetMaterialization("test")

    def _gen2():
        yield Output("done")

    def _gen():
        yield from _gen1()
        yield from _gen2()

    @op
    def gen_return_solid(_):
        return _gen()

    result = wrap_op_in_graph_and_execute(gen_return_solid)
    assert result.output_value() == "done"


def test_experimental_generator_solid():
    @op
    @experimental
    def gen_solid():
        yield Output("done")

    result = wrap_op_in_graph_and_execute(gen_solid)
    assert result.output_value() == "done"
