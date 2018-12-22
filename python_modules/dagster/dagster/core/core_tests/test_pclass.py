import pytest

from pyrsistent import (
    PClass,
    field,
    PTypeError,
)


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
