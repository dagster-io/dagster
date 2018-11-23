import uuid

import pytest

import dagstermill as dm

from dagster import (
    Field,
    SolidDefinition,
    InputDefinition,
    OutputDefinition,
    check,
    types,
)


def test_basic_get_in_memory_input():
    manager = dm.define_manager()
    inputs = manager.define_inputs(a=1)
    assert manager.get_input(inputs, 'a') == 1


def test_basic_get_in_memory_inputs():
    manager = dm.define_manager()
    inputs = manager.define_inputs(a=1, b=2)
    assert manager.get_input(inputs, 'a') == 1
    assert manager.get_input(inputs, 'b') == 2

    a, b = manager.get_inputs(inputs, 'a', 'b')

    assert a == 1
    assert b == 2


def test_basic_get_serialized_inputs():
    manager = dm.define_manager()
    output_path = '/tmp/dagstermill/temp_values/{some_id}'.format(some_id=str(uuid.uuid4()))
    inputs = dm.serialize_inputs(dict(a=1, b=2), input_defs=None, scratch_dir=output_path)
    assert manager.get_input(inputs, 'a') == 1
    assert manager.get_input(inputs, 'b') == 2

    a, b = manager.get_inputs(inputs, 'a', 'b')

    assert a == 1
    assert b == 2


def test_basic_in_memory_config():
    manager = dm.define_manager()
    value = {'path': 'some_path.csv'}
    config_ = manager.define_config(value)
    assert manager.get_config(config_) == value


def test_basic_serialized_config():
    manager = dm.define_manager()
    value = {'path': 'some_path.csv'}
    config_ = dm.serialize_dm_object(value)
    assert manager.get_config(config_) == value


def test_serialize_unserialize():
    value = {'a': 1, 'b': 2}
    assert dm.deserialize_dm_object(dm.serialize_dm_object(value)) == value


def define_solid_with_stuff():
    return SolidDefinition(
        name='stuff',
        inputs=[InputDefinition('foo', types.Int)],
        outputs=[OutputDefinition(name='bar', dagster_type=types.Int)],
        config_field=Field(types.Int),
        transform_fn=lambda *args, **kwargs: check.failed('do not execute'),
        metadata={
            'notebook_path': 'unused.ipynb',
            'kind': 'ipynb',
        },
    )


def test_input_names():
    manager = dm.define_manager(define_solid_with_stuff())
    manager.define_inputs(foo=2)

    with pytest.raises(dm.DagstermillError, match='Solid stuff does not have input baaz'):
        manager.define_inputs(baaz=2)


def test_input_typecheck():
    manager = dm.define_manager(define_solid_with_stuff())
    manager.define_inputs(foo=2)

    with pytest.raises(dm.DagstermillError, match='Input foo failed type check'):
        manager.define_inputs(foo='ndokfjdkf')


def test_output_name():
    manager = dm.define_manager(define_solid_with_stuff())

    with pytest.raises(dm.DagstermillError, match='Solid stuff does not have output named nope'):
        manager.yield_result(234, output_name='nope')

    with pytest.raises(dm.DagstermillError, match='Solid stuff does not have output named result'):
        manager.yield_result(234)


def test_output_typemismatch():
    manager = dm.define_manager(define_solid_with_stuff())

    with pytest.raises(
        dm.DagstermillError,
        match='Output bar output_type Int failed type check',
    ):
        manager.yield_result('not_a_string', output_name='bar')


def test_config_typecheck():
    manager = dm.define_manager(define_solid_with_stuff())
    manager.define_config(2)

    with pytest.raises(dm.DagstermillError, match='Config for solid stuff failed type check'):
        manager.define_config('2k3j4k3')


def test_serialize_inputs():
    output_path = '/tmp/dagstermill/temp_values/{some_id}'.format(some_id=str(uuid.uuid4()))
    output = dm.serialize_inputs(
        {
            'foo': 'value_for_foo',
            'bar': 123
        },
        [
            InputDefinition('foo'),
            InputDefinition('bar'),
        ],
        output_path,
    )
