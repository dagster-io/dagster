import string
from collections import namedtuple
from enum import Enum
from typing import NamedTuple, Set

import pytest
from dagster.check import CheckError, ParameterCheckError, inst_param, set_param
from dagster.serdes.errors import SerdesClassUsageError
from dagster.serdes.serdes import (
    DefaultEnumSerializer,
    DefaultNamedTupleSerializer,
    WhitelistMap,
    _deserialize_json_to_dagster_namedtuple,
    _pack_value,
    _serialize_dagster_namedtuple,
    _unpack_value,
    _whitelist_for_serdes,
    deserialize_json_to_dagster_namedtuple,
    deserialize_value,
    serialize_dagster_namedtuple,
    serialize_value,
)
from dagster.serdes.utils import create_snapshot_id


def test_deserialize_value_ok():
    unpacked_tuple = deserialize_value('{"foo": "bar"}')
    assert unpacked_tuple
    assert unpacked_tuple["foo"] == "bar"


def test_deserialize_json_to_dagster_namedtuple_non_namedtuple():
    with pytest.raises(CheckError):
        deserialize_json_to_dagster_namedtuple('{"foo": "bar"}')


@pytest.mark.parametrize("bad_obj", [1, None, False])
def test_deserialize_json_to_dagster_namedtuple_invalid_types(bad_obj):
    with pytest.raises(ParameterCheckError):
        deserialize_json_to_dagster_namedtuple(bad_obj)


def test_deserialize_empty_set():
    assert set() == deserialize_value(serialize_value(set()))
    assert frozenset() == deserialize_value(serialize_value(frozenset()))


def test_forward_compat_serdes_new_field_with_default():
    test_map = WhitelistMap()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Quux(namedtuple("_Quux", "foo bar")):
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)  # pylint: disable=bad-super-call

    assert test_map.has_tuple_entry("Quux")
    klass, _ = test_map.get_tuple_entry("Quux")
    assert klass is Quux

    quux = Quux("zip", "zow")

    serialized = _serialize_dagster_namedtuple(quux, whitelist_map=test_map)

    # pylint: disable=function-redefined
    @_whitelist_for_serdes(whitelist_map=test_map)
    class Quux(namedtuple("_Quux", "foo bar baz")):  # pylint: disable=bad-super-call
        def __new__(cls, foo, bar, baz=None):
            return super(Quux, cls).__new__(cls, foo, bar, baz=baz)

    assert test_map.has_tuple_entry("Quux")

    klass, _ = test_map.get_tuple_entry("Quux")
    assert klass is Quux

    deserialized = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=test_map)

    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert deserialized.baz is None


def test_forward_compat_serdes_new_enum_field():
    test_map = WhitelistMap()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Corge(Enum):
        FOO = 1
        BAR = 2

    assert test_map.has_enum_entry("Corge")

    corge = Corge.FOO

    packed = _pack_value(corge, whitelist_map=test_map)

    # pylint: disable=function-redefined
    @_whitelist_for_serdes(whitelist_map=test_map)
    class Corge(Enum):
        FOO = 1
        BAR = 2
        BAZ = 3

    unpacked = _unpack_value(packed, whitelist_map=test_map)

    assert unpacked != corge
    assert unpacked.name == corge.name
    assert unpacked.value == corge.value


def test_serdes_enum_backcompat():
    test_map = WhitelistMap()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Corge(Enum):
        FOO = 1
        BAR = 2

    assert test_map.has_enum_entry("Corge")

    corge = Corge.FOO

    packed = _pack_value(corge, whitelist_map=test_map)

    class CorgeBackCompatSerializer(DefaultEnumSerializer):
        @classmethod
        def value_from_storage_str(cls, storage_str, klass):
            if storage_str == "FOO":
                value = "FOO_FOO"
            else:
                value = storage_str

            return super().value_from_storage_str(value, klass)

    # pylint: disable=function-redefined
    @_whitelist_for_serdes(whitelist_map=test_map, serializer=CorgeBackCompatSerializer)
    class Corge(Enum):
        BAR = 2
        BAZ = 3
        FOO_FOO = 4

    unpacked = _unpack_value(packed, whitelist_map=test_map)

    assert unpacked != corge
    assert unpacked == Corge.FOO_FOO


def test_backward_compat_serdes():
    test_map = WhitelistMap()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Quux(namedtuple("_Quux", "foo bar baz")):
        def __new__(cls, foo, bar, baz):
            return super(Quux, cls).__new__(cls, foo, bar, baz)  # pylint: disable=bad-super-call

    quux = Quux("zip", "zow", "whoopie")

    serialized = _serialize_dagster_namedtuple(quux, whitelist_map=test_map)

    # pylint: disable=function-redefined
    @_whitelist_for_serdes(whitelist_map=test_map)
    class Quux(namedtuple("_Quux", "foo bar")):  # pylint: disable=bad-super-call
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)

    deserialized = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=test_map)

    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert not hasattr(deserialized, "baz")


def serdes_test_class(klass):
    test_map = WhitelistMap()

    return _whitelist_for_serdes(whitelist_map=test_map)(klass)


def test_wrong_first_arg():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class NotCls(namedtuple("NotCls", "field_one field_two")):
            def __new__(not_cls, field_two, field_one):
                return super(NotCls, not_cls).__new__(field_one, field_two)

    assert (
        str(exc_info.value)
        == 'For namedtuple NotCls: First parameter must be _cls or cls. Got "not_cls".'
    )


def test_incorrect_order():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class WrongOrder(namedtuple("WrongOrder", "field_one field_two")):
            def __new__(cls, field_two, field_one):
                return super(WrongOrder, cls).__new__(field_one, field_two)

    assert str(exc_info.value) == (
        "For namedtuple WrongOrder: "
        "Params to __new__ must match the order of field declaration "
        "in the namedtuple. Declared field number 1 in the namedtuple "
        'is "field_one". Parameter 1 in __new__ method is "field_two".'
    )


def test_missing_one_parameter():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class MissingFieldInNew(namedtuple("MissingFieldInNew", "field_one field_two field_three")):
            def __new__(cls, field_one, field_two):
                return super(MissingFieldInNew, cls).__new__(field_one, field_two, None)

    assert str(exc_info.value) == (
        "For namedtuple MissingFieldInNew: "
        "Missing parameters to __new__. You have declared fields in "
        "the named tuple that are not present as parameters to the "
        "to the __new__ method. In order for both serdes serialization "
        "and pickling to work, these must match. Missing: ['field_three']"
    )


def test_missing_many_parameters():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class MissingFieldsInNew(
            namedtuple("MissingFieldsInNew", "field_one field_two field_three, field_four")
        ):
            def __new__(cls, field_one, field_two):
                return super(MissingFieldsInNew, cls).__new__(field_one, field_two, None, None)

    assert str(exc_info.value) == (
        "For namedtuple MissingFieldsInNew: "
        "Missing parameters to __new__. You have declared fields in "
        "the named tuple that are not present as parameters to the "
        "to the __new__ method. In order for both serdes serialization "
        "and pickling to work, these must match. Missing: ['field_three', 'field_four']"
    )


def test_extra_parameters_must_have_defaults():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class OldFieldsWithoutDefaults(
            namedtuple("OldFieldsWithoutDefaults", "field_three field_four")
        ):
            # pylint:disable=unused-argument
            def __new__(
                cls,
                field_three,
                field_four,
                # Graveyard Below
                field_one,
                field_two,
            ):
                return super(OldFieldsWithoutDefaults, cls).__new__(field_three, field_four)

    assert str(exc_info.value) == (
        "For namedtuple OldFieldsWithoutDefaults: "
        'Parameter "field_one" is a parameter to the __new__ '
        "method but is not a field in this namedtuple. "
        "The only reason why this should exist is that "
        "it is a field that used to exist (we refer to "
        "this as the graveyard) but no longer does. However "
        "it might exist in historical storage. This parameter "
        "existing ensures that serdes continues to work. However "
        "these must come at the end and have a default value for pickling to work."
    )


def test_extra_parameters_have_working_defaults():
    @serdes_test_class
    class OldFieldsWithDefaults(namedtuple("OldFieldsWithDefaults", "field_three field_four")):
        # pylint:disable=unused-argument
        def __new__(
            cls,
            field_three,
            field_four,
            # Graveyard Below
            none_field=None,
            falsey_field=0,
            another_falsey_field="",
            value_field="klsjkfjd",
        ):
            return super(OldFieldsWithDefaults, cls).__new__(field_three, field_four)


def test_set():
    test_map = WhitelistMap()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class HasSets(namedtuple("_HasSets", "reg_set frozen_set")):
        def __new__(cls, reg_set, frozen_set):
            set_param(reg_set, "reg_set")
            inst_param(frozen_set, "frozen_set", frozenset)
            return super(HasSets, cls).__new__(cls, reg_set, frozen_set)

    foo = HasSets({1, 2, 3, "3"}, frozenset([4, 5, 6, "6"]))

    serialized = _serialize_dagster_namedtuple(foo, whitelist_map=test_map)
    foo_2 = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=test_map)
    assert foo == foo_2

    # verify that set elements are serialized in a consistent order so that
    # equal objects always have a consistent serialization / snapshot ID
    big_foo = HasSets(set(string.ascii_lowercase), frozenset(string.ascii_lowercase))

    assert create_snapshot_id(big_foo) == create_snapshot_id(
        _deserialize_json_to_dagster_namedtuple(
            _serialize_dagster_namedtuple(big_foo, whitelist_map=test_map), whitelist_map=test_map
        )
    )


def test_persistent_tuple():
    test_map = WhitelistMap()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Alphabet(namedtuple("_Alphabet", "a b c")):
        def __new__(cls, a, b, c):
            return super(Alphabet, cls).__new__(cls, a, b, c)

    foo = Alphabet(a="A", b="B", c="C")
    serialized = _serialize_dagster_namedtuple(foo, whitelist_map=test_map)
    foo_2 = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=test_map)
    assert foo == foo_2


def test_from_storage_dict():
    test_map = WhitelistMap()

    class CompatSerializer(DefaultNamedTupleSerializer):
        @classmethod
        def value_from_storage_dict(cls, storage_dict, klass):
            return DeprecatedAlphabet.legacy_load(storage_dict)

    @_whitelist_for_serdes(whitelist_map=test_map, serializer=CompatSerializer)
    class DeprecatedAlphabet(namedtuple("_DeprecatedAlphabet", "a b c")):
        def __new__(cls, a, b, c):
            raise Exception("DeprecatedAlphabet is deprecated")

        @classmethod
        def legacy_load(cls, storage_dict):
            # instead of the DeprecatedAlphabet, directly invoke the namedtuple constructor
            return super().__new__(
                cls,
                storage_dict.get("a"),
                storage_dict.get("b"),
                storage_dict.get("c"),
            )

    serialized = '{"__class__": "DeprecatedAlphabet", "a": "A", "b": "B", "c": "C"}'

    nt = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=test_map)
    assert isinstance(nt, DeprecatedAlphabet)


def test_skip_when_empty():
    test_map = WhitelistMap()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class SameSnapshotTuple(namedtuple("_Tuple", "foo")):
        def __new__(cls, foo):
            return super(SameSnapshotTuple, cls).__new__(cls, foo)  # pylint: disable=bad-super-call

    old_tuple = SameSnapshotTuple(foo="A")
    old_serialized = serialize_dagster_namedtuple(old_tuple)
    old_snapshot = create_snapshot_id(old_tuple)

    # Without setting skip_when_empty, the ID changes

    @_whitelist_for_serdes(whitelist_map=test_map)
    class SameSnapshotTuple(namedtuple("_Tuple", "foo bar")):  # pylint: disable=function-redefined
        def __new__(cls, foo, bar=None):
            return super(SameSnapshotTuple, cls).__new__(  # pylint: disable=bad-super-call
                cls, foo, bar
            )

    new_tuple_without_serializer = SameSnapshotTuple(foo="A")
    new_snapshot_without_serializer = create_snapshot_id(new_tuple_without_serializer)

    assert new_snapshot_without_serializer != old_snapshot

    # By setting a custom serializer and skip_when_empty, the snapshot stays the same
    # as long as the new field is None

    class SkipWhenEmptySerializer(DefaultNamedTupleSerializer):
        @classmethod
        def skip_when_empty(cls) -> Set[str]:
            return {"bar"}

    @_whitelist_for_serdes(whitelist_map=test_map, serializer=SkipWhenEmptySerializer)
    class SameSnapshotTuple(namedtuple("_Tuple", "foo bar")):  # pylint: disable=function-redefined
        def __new__(cls, foo, bar=None):
            return super(SameSnapshotTuple, cls).__new__(  # pylint: disable=bad-super-call
                cls, foo, bar
            )

    new_tuple = SameSnapshotTuple(foo="A")
    new_snapshot = create_snapshot_id(new_tuple)

    assert old_snapshot == new_snapshot

    rehydrated_tuple = deserialize_json_to_dagster_namedtuple(old_serialized)
    assert rehydrated_tuple.foo == "A"
    assert rehydrated_tuple.bar is None

    new_tuple_with_bar = SameSnapshotTuple(foo="A", bar="B")
    assert new_tuple_with_bar.foo == "A"
    assert new_tuple_with_bar.bar == "B"


def test_to_storage_value():
    test_map = WhitelistMap()

    class MySerializer(DefaultNamedTupleSerializer):
        @classmethod
        def value_to_storage_dict(cls, value, whitelist_map):
            return DefaultNamedTupleSerializer.value_to_storage_dict(
                SubstituteAlphabet(value.a, value.b, value.c), test_map
            )

    @_whitelist_for_serdes(whitelist_map=test_map, serializer=MySerializer)
    class DeprecatedAlphabet(namedtuple("_DeprecatedAlphabet", "a b c")):
        def __new__(cls, a, b, c):
            return super(DeprecatedAlphabet, cls).__new__(cls, a, b, c)

    @_whitelist_for_serdes(whitelist_map=test_map)
    class SubstituteAlphabet(namedtuple("_SubstituteAlphabet", "a b c")):
        def __new__(cls, a, b, c):
            return super(SubstituteAlphabet, cls).__new__(cls, a, b, c)

    nested = DeprecatedAlphabet(None, None, "_C")
    deprecated = DeprecatedAlphabet("A", "B", nested)
    serialized = _serialize_dagster_namedtuple(deprecated, whitelist_map=test_map)
    alphabet = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=test_map)
    assert not isinstance(alphabet, DeprecatedAlphabet)
    assert isinstance(alphabet, SubstituteAlphabet)
    assert not isinstance(alphabet.c, DeprecatedAlphabet)
    assert isinstance(alphabet.c, SubstituteAlphabet)


def test_long_int():
    test_map = WhitelistMap()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class NumHolder(NamedTuple):
        num: int

    x = NumHolder(98765432109876543210)
    ser_x = _serialize_dagster_namedtuple(x, test_map)
    roundtrip_x = _deserialize_json_to_dagster_namedtuple(ser_x, test_map)
    assert x.num == roundtrip_x.num
