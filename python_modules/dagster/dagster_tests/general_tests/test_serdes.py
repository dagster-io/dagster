import sys
from collections import namedtuple
from enum import Enum

import pytest
from dagster.check import CheckError, ParameterCheckError, inst_param, set_param
from dagster.serdes import (
    Persistable,
    SerdesClassUsageError,
    _deserialize_json_to_dagster_namedtuple,
    _pack_value,
    _serialize_dagster_namedtuple,
    _unpack_value,
    _whitelist_for_persistence,
    _whitelist_for_serdes,
    default_to_storage_value,
    deserialize_json_to_dagster_namedtuple,
    deserialize_value,
    serialize_value,
)
from dagster.utils import compose


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


def _initial_whitelist_map():
    return {
        "types": {"tuple": {}, "enum": {}},
        "persistence": {},
    }


def test_forward_compat_serdes_new_field_with_default():
    _TEST_WHITELIST_MAP = _initial_whitelist_map()

    @_whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP)
    class Quux(namedtuple("_Quux", "foo bar")):
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)  # pylint: disable=bad-super-call

    assert "Quux" in _TEST_WHITELIST_MAP["types"]["tuple"]
    assert _TEST_WHITELIST_MAP["types"]["tuple"]["Quux"] == Quux

    quux = Quux("zip", "zow")

    serialized = _serialize_dagster_namedtuple(quux, whitelist_map=_TEST_WHITELIST_MAP)

    # pylint: disable=function-redefined
    @_whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP)
    class Quux(namedtuple("_Quux", "foo bar baz")):  # pylint: disable=bad-super-call
        def __new__(cls, foo, bar, baz=None):
            return super(Quux, cls).__new__(cls, foo, bar, baz=baz)

    assert "Quux" in _TEST_WHITELIST_MAP["types"]["tuple"]
    assert _TEST_WHITELIST_MAP["types"]["tuple"]["Quux"] == Quux

    deserialized = _deserialize_json_to_dagster_namedtuple(
        serialized, whitelist_map=_TEST_WHITELIST_MAP
    )
    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert deserialized.baz is None


def test_forward_compat_serdes_new_enum_field():
    _TEST_WHITELIST_MAP = _initial_whitelist_map()

    @_whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP)
    class Corge(Enum):
        FOO = 1
        BAR = 2

    assert "Corge" in _TEST_WHITELIST_MAP["types"]["enum"]

    corge = Corge.FOO

    packed = _pack_value(corge, whitelist_map=_TEST_WHITELIST_MAP)

    # pylint: disable=function-redefined
    @_whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP)
    class Corge(Enum):
        FOO = 1
        BAR = 2
        BAZ = 3

    unpacked = _unpack_value(packed, whitelist_map=_TEST_WHITELIST_MAP)

    assert unpacked != corge
    assert unpacked.name == corge.name
    assert unpacked.value == corge.value


def test_backward_compat_serdes():
    _TEST_WHITELIST_MAP = _initial_whitelist_map()

    @_whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP)
    class Quux(namedtuple("_Quux", "foo bar baz")):
        def __new__(cls, foo, bar, baz):
            return super(Quux, cls).__new__(cls, foo, bar, baz)  # pylint: disable=bad-super-call

    quux = Quux("zip", "zow", "whoopie")

    serialized = _serialize_dagster_namedtuple(quux, whitelist_map=_TEST_WHITELIST_MAP)

    # pylint: disable=function-redefined
    @_whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP)
    class Quux(namedtuple("_Quux", "foo bar")):  # pylint: disable=bad-super-call
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)

    deserialized = _deserialize_json_to_dagster_namedtuple(
        serialized, whitelist_map=_TEST_WHITELIST_MAP
    )

    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert not hasattr(deserialized, "baz")


def serdes_test_class(klass):
    _TEST_WHITELIST_MAP = _initial_whitelist_map()

    return _whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP)(klass)


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


@pytest.mark.skipif(
    sys.version_info.major < 3, reason="Serdes declaration time checks python 3 only"
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


@pytest.mark.skipif(
    sys.version_info.major < 3, reason="Serdes declaration time checks python 3 only"
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
    _TEST_WHITELIST_MAP = _initial_whitelist_map()

    @_whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP)
    class HasSets(namedtuple("_HasSets", "reg_set frozen_set")):
        def __new__(cls, reg_set, frozen_set):
            set_param(reg_set, "reg_set")
            inst_param(frozen_set, "frozen_set", frozenset)
            return super(HasSets, cls).__new__(cls, reg_set, frozen_set)

    foo = HasSets({1, 2, 3, "3"}, frozenset([4, 5, 6, "6"]))

    serialized = _serialize_dagster_namedtuple(foo, whitelist_map=_TEST_WHITELIST_MAP)
    foo_2 = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=_TEST_WHITELIST_MAP)
    assert foo == foo_2


def test_persistent_tuple():
    _TEST_WHITELIST_MAP = _initial_whitelist_map()

    def whitelist_for_persistence(klass):
        return compose(
            _whitelist_for_persistence(whitelist_map=_TEST_WHITELIST_MAP),
            _whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP),
        )(klass)

    @whitelist_for_persistence
    class Alphabet(namedtuple("_Alphabet", "a b c"), Persistable):
        def __new__(cls, a, b, c):
            return super(Alphabet, cls).__new__(cls, a, b, c)

    foo = Alphabet(a="A", b="B", c="C")
    serialized = _serialize_dagster_namedtuple(foo, whitelist_map=_TEST_WHITELIST_MAP)
    foo_2 = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=_TEST_WHITELIST_MAP)
    assert foo == foo_2


def test_from_storage_dict():
    _TEST_WHITELIST_MAP = _initial_whitelist_map()

    def whitelist_for_persistence(klass):
        return compose(
            _whitelist_for_persistence(whitelist_map=_TEST_WHITELIST_MAP),
            _whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP),
        )(klass)

    @whitelist_for_persistence
    class DeprecatedAlphabet(namedtuple("_DeprecatedAlphabet", "a b c"), Persistable):
        def __new__(cls, a, b, c):
            raise Exception("DeprecatedAlphabet is deprecated")

        @classmethod
        def from_storage_dict(cls, storage_dict):
            # instead of the DeprecatedAlphabet, directly invoke the namedtuple constructor
            return super(DeprecatedAlphabet, cls).__new__(
                cls,
                storage_dict.get("a"),
                storage_dict.get("b"),
                storage_dict.get("c"),
            )

    assert "DeprecatedAlphabet" in _TEST_WHITELIST_MAP["persistence"]
    serialized = '{"__class__": "DeprecatedAlphabet", "a": "A", "b": "B", "c": "C"}'

    nt = _deserialize_json_to_dagster_namedtuple(serialized, whitelist_map=_TEST_WHITELIST_MAP)
    assert isinstance(nt, DeprecatedAlphabet)


def test_to_storage_value():
    _TEST_WHITELIST_MAP = _initial_whitelist_map()

    def whitelist_for_persistence(klass):
        return compose(
            _whitelist_for_persistence(whitelist_map=_TEST_WHITELIST_MAP),
            _whitelist_for_serdes(whitelist_map=_TEST_WHITELIST_MAP),
        )(klass)

    @whitelist_for_persistence
    class DeprecatedAlphabet(namedtuple("_DeprecatedAlphabet", "a b c"), Persistable):
        def __new__(cls, a, b, c):
            return super(DeprecatedAlphabet, cls).__new__(cls, a, b, c)

        def to_storage_value(self):
            return default_to_storage_value(
                SubstituteAlphabet(self.a, self.b, self.c), _TEST_WHITELIST_MAP
            )

    @whitelist_for_persistence
    class SubstituteAlphabet(namedtuple("_SubstituteAlphabet", "a b c"), Persistable):
        def __new__(cls, a, b, c):
            return super(SubstituteAlphabet, cls).__new__(cls, a, b, c)

    nested = DeprecatedAlphabet(None, None, "_C")
    deprecated = DeprecatedAlphabet("A", "B", nested)
    serialized = _serialize_dagster_namedtuple(deprecated, whitelist_map=_TEST_WHITELIST_MAP)
    alphabet = _deserialize_json_to_dagster_namedtuple(
        serialized, whitelist_map=_TEST_WHITELIST_MAP
    )
    assert not isinstance(alphabet, DeprecatedAlphabet)
    assert isinstance(alphabet, SubstituteAlphabet)
    assert not isinstance(alphabet.c, DeprecatedAlphabet)
    assert isinstance(alphabet.c, SubstituteAlphabet)
