from dagster import AssetMaterialization, Output, op
from dagster._annotations import experimental
from dagster._legacy import execute_solid


def test_generator_return_solid():
    def _gen():
        yield Output("done")

    @op
    def gen_ret_op(_):
        return _gen()

    result = execute_solid(gen_ret_op)
    assert result.output_value() == "done"


def test_generator_yield_solid():
    def _gen():
        yield Output("done")

    @op
    def gen_yield_op(_):
        for event in _gen():
            yield event

    result = execute_solid(gen_yield_op)
    assert result.output_value() == "done"


def test_generator_yield_from_solid():
    def _gen():
        yield Output("done")

    @op
    def gen_yield_op(_):
        yield from _gen()

    result = execute_solid(gen_yield_op)
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
    def gen_return_op(_):
        return _gen()

    result = execute_solid(gen_return_op)
    assert result.output_value() == "done"


def test_experimental_generator_solid():
    @op
    @experimental
    def gen_op():
        yield Output("done")

    result = execute_solid(gen_op)
    assert result.output_value() == "done"
