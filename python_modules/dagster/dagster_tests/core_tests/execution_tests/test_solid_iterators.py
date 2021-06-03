from dagster import AssetMaterialization, Output, execute_solid, solid
from dagster.utils.backcompat import experimental


def test_generator_return_solid():
    def _gen():
        yield Output("done")

    @solid
    def gen_ret_solid(_):
        return _gen()

    result = execute_solid(gen_ret_solid)
    assert result.output_value() == "done"


def test_generator_yield_solid():
    def _gen():
        yield Output("done")

    @solid
    def gen_yield_solid(_):
        for event in _gen():
            yield event

    result = execute_solid(gen_yield_solid)
    assert result.output_value() == "done"


def test_generator_yield_from_solid():
    def _gen():
        yield Output("done")

    @solid
    def gen_yield_solid(_):
        yield from _gen()

    result = execute_solid(gen_yield_solid)
    assert result.output_value() == "done"


def test_nested_generator_solid():
    def _gen1():
        yield AssetMaterialization("test")

    def _gen2():
        yield Output("done")

    def _gen():
        yield from _gen1()
        yield from _gen2()

    @solid
    def gen_return_solid(_):
        return _gen()

    result = execute_solid(gen_return_solid)
    assert result.output_value() == "done"


def test_experimental_generator_solid():
    @solid
    @experimental
    def gen_solid():
        yield Output("done")

    result = execute_solid(gen_solid)
    assert result.output_value() == "done"
