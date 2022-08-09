from dagster import op


def test_single_input():
    @op
    def add_one(_context, num):
        return num + 1

    assert add_one
    assert len(add_one.ins) == 1
    assert list(add_one.ins.keys())[0] == "num"
    assert add_one.ins["num"].dagster_type.unique_name == "Any"


def test_double_input():
    @op
    def subtract(_context, num_one, num_two):
        return num_one + num_two

    assert subtract
    assert len(subtract.ins) == 2
    assert list(subtract.ins.keys())[0] == "num_one"
    assert subtract.ins["num_one"].dagster_type.unique_name == "Any"

    assert list(subtract.ins.keys())[1] == "num_two"
    assert subtract.ins["num_two"].dagster_type.unique_name == "Any"
