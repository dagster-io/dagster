import json
import pytest

from pyrsistent import (
    PClass,
    field,
    PTypeError,
)

from dagster import types

from dagster.core.execution_plan.objects import (
    StepInput,
    StepInputMeta,
    StepOutputMeta,
    StepOutputHandle,
)

# Generic PClass Testing (delete at some point)


class FooBar(PClass):
    foo = field(type=int)
    bar = field(type=int)

    @property
    def added(self):
        return self.foo + self.bar


def test_foobar():
    obj = FooBar(foo=1, bar=2)
    assert obj.foo == 1
    assert obj.bar == 2


def test_typeerror():
    with pytest.raises(PTypeError):
        FooBar(foo='djfkkd', bar=2)


def test_serialize_cycle():
    obj = FooBar(foo=1, bar=2)
    assert obj.serialize() == {'foo': 1, 'bar': 2}
    obj_serialize_cycled = FooBar.create(obj.serialize())
    assert obj_serialize_cycled == obj
    assert obj_serialize_cycled.serialize() == {'foo': 1, 'bar': 2}


def test_derived():
    obj = FooBar(foo=1, bar=2)
    assert obj.added == 3


def test_repr():
    obj = FooBar(foo=1, bar=2)
    print(repr(obj))


# Execution Plan Testing


def json_round_trip(cls, thing):
    return cls.create(json.loads(json.dumps(thing.serialize())))


def test_step_output_meta():
    meta = StepOutputMeta(name='some_output', dagster_type_name='Int')
    assert meta.serialize() == {'name': 'some_output', 'dagster_type_name': 'Int'}
    assert StepOutputMeta.create(meta.serialize()) == meta
    assert json_round_trip(StepOutputHandle, meta) == meta


def test_step_input_meta():
    meta = StepInputMeta(
        name='some_input',
        dagster_type_name='Int',
        prev_output_handle=StepOutputHandle(
            step_key='prev_step',
            output_name='prev_output',
        )
    )
    assert meta.serialize() == {
        'name': 'some_input',
        'dagster_type_name': 'Int',
        'prev_output_handle': {
            'step_key': 'prev_step',
            'output_name': 'prev_output'
        }
    }
    assert StepInputMeta.create(meta.serialize()) == meta
    assert json_round_trip(StepInputMeta, meta) == meta


def test_step_input_failed():
    step_input = StepInput.from_props(
        'some_input', types.Int, StepOutputHandle(
            step_key='prev_step',
            output_name='prev_output',
        )
    )

    with pytest.raises(TypeError):
        assert json_round_trip(StepInput, step_input) == step_input
