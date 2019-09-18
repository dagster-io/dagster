import sys
from collections import namedtuple
from enum import Enum

import pytest

from dagster.core.serdes import (
    _deserialize_json_to_dagster_namedtuple,
    _pack_value,
    _serialize_dagster_namedtuple,
    _unpack_value,
    _whitelist_for_serdes,
)


def test_forward_compat_serdes_new_field_with_default():
    _TEST_TUPLE_MAP = {}
    _TEST_ENUM_MAP = {}

    @_whitelist_for_serdes(tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)
    class Quux(namedtuple('_Quux', 'foo bar')):
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)  # pylint: disable=bad-super-call

    assert 'Quux' in _TEST_TUPLE_MAP
    assert _TEST_TUPLE_MAP['Quux'] == Quux

    quux = Quux('zip', 'zow')

    serialized = _serialize_dagster_namedtuple(
        quux, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )

    @_whitelist_for_serdes(
        tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )  # pylint: disable=function-redefined
    class Quux(namedtuple('_Quux', 'foo bar baz')):  # pylint: disable=bad-super-call
        def __new__(cls, foo, bar, baz=None):
            return super(Quux, cls).__new__(cls, foo, bar, baz=baz)

    assert 'Quux' in _TEST_TUPLE_MAP
    assert _TEST_TUPLE_MAP['Quux'] == Quux

    deserialized = _deserialize_json_to_dagster_namedtuple(
        serialized, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )

    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert deserialized.baz is None


def test_forward_compat_serdes_new_enum_field():
    _TEST_TUPLE_MAP = {}
    _TEST_ENUM_MAP = {}

    @_whitelist_for_serdes(tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)
    class Corge(Enum):
        FOO = 1
        BAR = 2

    assert 'Corge' in _TEST_ENUM_MAP

    corge = Corge.FOO

    packed = _pack_value(corge, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)

    @_whitelist_for_serdes(
        tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )  # pylint: disable=function-redefined
    class Corge(Enum):
        FOO = 1
        BAR = 2
        BAZ = 3

    unpacked = _unpack_value(packed, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)

    assert unpacked != corge
    assert unpacked.name == corge.name
    assert unpacked.value == corge.value


# This behavior isn't possible on 2.7 because of `inspect` limitations
@pytest.mark.skipif(sys.version_info < (3,), reason="This behavior isn't available on 2.7")
def test_backward_compat_serdes():
    _TEST_TUPLE_MAP = {}
    _TEST_ENUM_MAP = {}

    @_whitelist_for_serdes(tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)
    class Quux(namedtuple('_Quux', 'foo bar baz')):
        def __new__(cls, foo, bar, baz):
            return super(Quux, cls).__new__(cls, foo, bar, baz)  # pylint: disable=bad-super-call

    quux = Quux('zip', 'zow', 'whoopie')

    serialized = _serialize_dagster_namedtuple(
        quux, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )

    @_whitelist_for_serdes(
        tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )  # pylint: disable=function-redefined
    class Quux(namedtuple('_Quux', 'foo bar')):  # pylint: disable=bad-super-call
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)

    deserialized = _deserialize_json_to_dagster_namedtuple(
        serialized, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )

    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert not hasattr(deserialized, 'baz')
