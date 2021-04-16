from dagster import InputDefinition, solid


def test_flex_inputs():
    @solid(input_defs=[InputDefinition("arg_b", metadata={"explicit": True})])
    def partial(_context, arg_a, arg_b):
        return arg_a + arg_b

    assert partial.input_defs[0].name == "arg_b"
    assert partial.input_defs[0].metadata["explicit"]
    assert partial.input_defs[1].name == "arg_a"
