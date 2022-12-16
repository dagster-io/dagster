from dagster import op


def test_single_input():
    @op
    def add_one(_context, num):
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == "num"
    assert add_one.input_defs[0].dagster_type.unique_name == "Any"


def test_double_input():
    @op
    def subtract(_context, num_one, num_two):
        return num_one + num_two

    assert subtract
    assert len(subtract.input_defs) == 2
    assert subtract.input_defs[0].name == "num_one"
    assert subtract.input_defs[0].dagster_type.unique_name == "Any"

    assert subtract.input_defs[1].name == "num_two"
    assert subtract.input_defs[1].dagster_type.unique_name == "Any"
