from dagster import lambda_solid, solid


def test_single_input():
    @solid
    def add_one(_context, num):
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == 'num'
    assert add_one.input_defs[0].runtime_type.name == 'Any'


def test_double_input():
    @solid
    def add(_context, num_one, num_two):
        return num_one + num_two

    assert add
    assert len(add.input_defs) == 2
    assert add.input_defs[0].name == 'num_one'
    assert add.input_defs[0].runtime_type.name == 'Any'

    assert add.input_defs[1].name == 'num_two'
    assert add.input_defs[1].runtime_type.name == 'Any'


def test_noop_lambda_solid():
    @lambda_solid
    def noop():
        pass

    assert noop
    assert len(noop.input_defs) == 0
    assert len(noop.output_defs) == 1


def test_one_arg_lambda_solid():
    @lambda_solid
    def one_arg(num):
        return num

    assert one_arg
    assert len(one_arg.input_defs) == 1
    assert one_arg.input_defs[0].name == 'num'
    assert one_arg.input_defs[0].runtime_type.name == 'Any'
    assert len(one_arg.output_defs) == 1
