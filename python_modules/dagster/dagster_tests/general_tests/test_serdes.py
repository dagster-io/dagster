import re
import string
from collections import namedtuple
from enum import Enum
from typing import Any, Dict, Mapping, NamedTuple, Optional, Sequence

import pytest
from dagster._check import ParameterCheckError, inst_param, set_param
from dagster._serdes.errors import DeserializationError, SerdesUsageError, SerializationError
from dagster._serdes.serdes import (
    EnumSerializer,
    FieldSerializer,
    NamedTupleSerializer,
    WhitelistMap,
    _whitelist_for_serdes,
    deserialize_value,
    serialize_value,
)
from dagster._serdes.utils import hash_str


def test_deserialize_value_ok():
    unpacked_tuple = deserialize_value('{"foo": "bar"}', as_type=dict)
    assert unpacked_tuple
    assert unpacked_tuple["foo"] == "bar"


def test_deserialize_json_non_namedtuple():
    with pytest.raises(DeserializationError, match="was not expected type"):
        deserialize_value('{"foo": "bar"}', NamedTuple)


@pytest.mark.parametrize("bad_obj", [1, None, False])
def test_deserialize_json_invalid_types(bad_obj):
    with pytest.raises(ParameterCheckError):
        deserialize_value(bad_obj)


def test_deserialize_empty_set():
    assert set() == deserialize_value(serialize_value(set()))
    assert frozenset() == deserialize_value(serialize_value(frozenset()))


def test_descent_path():
    class Foo(NamedTuple):
        bar: int

    with pytest.raises(SerializationError, match=re.escape("Descent path: <root:dict>.a.b[2].c")):
        serialize_value({"a": {"b": [{}, {}, {"c": Foo(1)}]}})

    test_map = WhitelistMap.create()
    blank_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Fizz(NamedTuple):
        buzz: int

    # Arg is not actually a namedtuple but the function still works on it
    ser = serialize_value({"a": {"b": [{}, {}, {"c": Fizz(1)}]}}, whitelist_map=test_map)

    with pytest.raises(DeserializationError, match=re.escape("Descent path: <root:dict>.a.b[2].c")):
        deserialize_value(ser, whitelist_map=blank_map)


def test_forward_compat_serdes_new_field_with_default():
    test_map = WhitelistMap.create()

    # Separate scope since we redefine Quux
    def get_orig_obj() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class Quux(NamedTuple("_Quux", [("foo", str), ("bar", str)])):
            def __new__(cls, foo, bar):
                return super(Quux, cls).__new__(cls, foo, bar)

        assert test_map.has_tuple_entry("Quux")
        serializer = test_map.get_tuple_entry("Quux")
        assert serializer.klass is Quux
        return Quux("zip", "zow")

    orig = get_orig_obj()
    serialized = serialize_value(orig, whitelist_map=test_map)

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Quux(NamedTuple("_Quux", [("foo", str), ("bar", str), ("baz", Optional[str])])):
        def __new__(cls, foo, bar, baz=None):
            return super(Quux, cls).__new__(cls, foo, bar, baz=baz)

    assert test_map.has_tuple_entry("Quux")
    serializer_v2 = test_map.get_tuple_entry("Quux")
    assert serializer_v2.klass is Quux

    deserialized = deserialize_value(serialized, as_type=Quux, whitelist_map=test_map)

    assert deserialized != orig
    assert deserialized.foo == orig.foo
    assert deserialized.bar == orig.bar
    assert deserialized.baz is None


def test_forward_compat_serdes_new_enum_field():
    test_map = WhitelistMap.create()

    # Separate scope since we redefine Corge
    def get_orig_obj() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class Corge(Enum):
            FOO = 1
            BAR = 2

        assert test_map.has_enum_entry("Corge")
        return Corge.FOO

    corge = get_orig_obj()
    serialized = serialize_value(corge, whitelist_map=test_map)

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Corge(Enum):
        FOO = 1
        BAR = 2
        BAZ = 3

    deserialized = deserialize_value(serialized, as_type=Corge, whitelist_map=test_map)

    assert deserialized != corge
    assert deserialized.name == corge.name
    assert deserialized.value == corge.value


def test_serdes_enum_backcompat():
    test_map = WhitelistMap.create()

    # Separate scope since we redefine Corge
    def get_orig_obj() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class Corge(Enum):
            FOO = 1
            BAR = 2

        assert test_map.has_enum_entry("Corge")
        return Corge.FOO

    corge = get_orig_obj()
    serialized = serialize_value(corge, whitelist_map=test_map)

    class CorgeBackCompatSerializer(EnumSerializer):
        def unpack(self, value):
            if value == "FOO":
                value = "FOO_FOO"
            else:
                value = value

            return super().unpack(value)

    @_whitelist_for_serdes(whitelist_map=test_map, serializer=CorgeBackCompatSerializer)
    class Corge(Enum):
        BAR = 2
        BAZ = 3
        FOO_FOO = 4

    deserialized = deserialize_value(serialized, whitelist_map=test_map)

    assert deserialized != corge
    assert deserialized == Corge.FOO_FOO


def test_backward_compat_serdes():
    test_map = WhitelistMap.create()

    # Separate scope since we redefine Quux
    def get_orig_obj() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class Quux(namedtuple("_Quux", "foo bar baz")):
            def __new__(cls, foo, bar, baz):
                return super(Quux, cls).__new__(cls, foo, bar, baz)

        return Quux("zip", "zow", "whoopie")

    quux = get_orig_obj()
    serialized = serialize_value(quux, whitelist_map=test_map)

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Quux(namedtuple("_Quux", "foo bar")):
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)

    deserialized = deserialize_value(serialized, as_type=Quux, whitelist_map=test_map)

    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert not hasattr(deserialized, "baz")


def test_forward_compat():
    old_map = WhitelistMap.create()

    # Separate scope since we redefine Quux
    def register_orig() -> Any:
        @_whitelist_for_serdes(whitelist_map=old_map)
        class Quux(namedtuple("_Quux", "bar baz")):
            def __new__(cls, bar, baz):
                return super().__new__(cls, bar, baz)

        return Quux

    orig_klass = register_orig()

    # new version has a new field with a new type
    new_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=new_map)
    class Quux(namedtuple("_Quux", "foo bar baz")):
        def __new__(cls, foo, bar, baz):
            return super().__new__(cls, foo, bar, baz)

    @_whitelist_for_serdes(whitelist_map=new_map)
    class Foo(namedtuple("_Foo", "wow")):
        def __new__(cls, wow):
            return super().__new__(cls, wow)

    new_quux = Quux(foo=Foo("wow"), bar="bar", baz="baz")

    # write from new
    serialized = serialize_value(new_quux, whitelist_map=new_map)

    # read from old, foo ignored
    deserialized = deserialize_value(serialized, as_type=orig_klass, whitelist_map=old_map)
    assert deserialized.bar == "bar"
    assert deserialized.baz == "baz"


def serdes_test_class(klass):
    test_map = WhitelistMap.create()

    return _whitelist_for_serdes(whitelist_map=test_map)(klass)


def test_wrong_first_arg():
    with pytest.raises(SerdesUsageError) as exc_info:

        @serdes_test_class
        class NotCls(namedtuple("NotCls", "field_one field_two")):
            def __new__(not_cls, field_two, field_one):  # type: ignore
                return super(NotCls, not_cls).__new__(field_one, field_two)

    assert (
        str(exc_info.value)
        == 'For namedtuple NotCls: First parameter must be _cls or cls. Got "not_cls".'
    )


def test_incorrect_order():
    with pytest.raises(SerdesUsageError) as exc_info:

        @serdes_test_class
        class WrongOrder(namedtuple("WrongOrder", "field_one field_two")):
            def __new__(cls, field_two, field_one):
                return super(WrongOrder, cls).__new__(field_one, field_two)

    assert (
        str(exc_info.value)
        == "For namedtuple WrongOrder: "
        "Params to __new__ must match the order of field declaration "
        "in the namedtuple. Declared field number 1 in the namedtuple "
        'is "field_one". Parameter 1 in __new__ method is "field_two".'
    )


def test_missing_one_parameter():
    with pytest.raises(SerdesUsageError) as exc_info:

        @serdes_test_class
        class MissingFieldInNew(namedtuple("MissingFieldInNew", "field_one field_two field_three")):
            def __new__(cls, field_one, field_two):
                return super(MissingFieldInNew, cls).__new__(field_one, field_two, None)

    assert (
        str(exc_info.value)
        == "For namedtuple MissingFieldInNew: "
        "Missing parameters to __new__. You have declared fields in "
        "the named tuple that are not present as parameters to the "
        "to the __new__ method. In order for both serdes serialization "
        "and pickling to work, these must match. Missing: ['field_three']"
    )


def test_missing_many_parameters():
    with pytest.raises(SerdesUsageError) as exc_info:

        @serdes_test_class
        class MissingFieldsInNew(
            namedtuple("MissingFieldsInNew", "field_one field_two field_three, field_four")
        ):
            def __new__(cls, field_one, field_two):
                return super(MissingFieldsInNew, cls).__new__(field_one, field_two, None, None)

    assert (
        str(exc_info.value)
        == "For namedtuple MissingFieldsInNew: "
        "Missing parameters to __new__. You have declared fields in "
        "the named tuple that are not present as parameters to the "
        "to the __new__ method. In order for both serdes serialization "
        "and pickling to work, these must match. Missing: ['field_three', 'field_four']"
    )


def test_extra_parameters_must_have_defaults():
    with pytest.raises(SerdesUsageError) as exc_info:

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

    assert (
        str(exc_info.value)
        == "For namedtuple OldFieldsWithoutDefaults: "
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
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class HasSets(namedtuple("_HasSets", "reg_set frozen_set")):
        def __new__(cls, reg_set, frozen_set):
            set_param(reg_set, "reg_set")
            inst_param(frozen_set, "frozen_set", frozenset)
            return super(HasSets, cls).__new__(cls, reg_set, frozen_set)

    foo = HasSets({1, 2, 3, "3"}, frozenset([4, 5, 6, "6"]))

    serialized = serialize_value(foo, whitelist_map=test_map)
    foo_2 = deserialize_value(serialized, whitelist_map=test_map)
    assert foo == foo_2

    # verify that set elements are serialized in a consistent order so that
    # equal objects always have a consistent serialization / snapshot ID
    big_foo = HasSets(set(string.ascii_lowercase), frozenset(string.ascii_lowercase))

    snap_id = hash_str(serialize_value(big_foo, whitelist_map=test_map))
    roundtrip_snap_id = hash_str(
        serialize_value(
            deserialize_value(
                serialize_value(big_foo, whitelist_map=test_map),
                whitelist_map=test_map,
            ),
            whitelist_map=test_map,
        )
    )
    assert snap_id == roundtrip_snap_id


def test_named_tuple() -> None:
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Foo(NamedTuple):
        color: str

    val = Foo("red")
    serialized = serialize_value(val, whitelist_map=test_map)
    deserialized = deserialize_value(serialized, whitelist_map=test_map)
    assert deserialized == val


def test_named_tuple_storage_name() -> None:
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env, storage_name="Bar")
    class Foo(NamedTuple):
        color: str

    val = Foo("red")
    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__class__": "Bar", "color": "red"}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == val


def test_named_tuple_old_storage_names() -> None:
    legacy_env = WhitelistMap.create()

    @_whitelist_for_serdes(legacy_env)
    class OldFoo(NamedTuple):
        color: str

    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env, old_storage_names={"OldFoo"})
    class Foo(NamedTuple):
        color: str

    val = Foo("red")
    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__class__": "Foo", "color": "red"}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == val

    old_serialized = serialize_value(OldFoo("red"), whitelist_map=legacy_env)
    old_deserialized = deserialize_value(old_serialized, whitelist_map=test_env)
    assert old_deserialized == val


def test_named_tuple_storage_field_names() -> None:
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env, storage_field_names={"color": "colour"})
    class Foo(NamedTuple):
        color: str

    val = Foo("red")
    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__class__": "Foo", "colour": "red"}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == val


def test_named_tuple_old_fields() -> None:
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env, old_fields={"shape": None})
    class Foo(NamedTuple):
        color: str

    val = Foo("red")
    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__class__": "Foo", "color": "red", "shape": null}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == val


def test_named_tuple_field_serializers() -> None:
    test_env = WhitelistMap.create()

    class PairsSerializer(FieldSerializer):
        def pack(
            self, entries: Mapping[str, str], whitelist_map: WhitelistMap, descent_path: str
        ) -> Sequence[Sequence[str]]:
            return list(entries.items())

        def unpack(
            self, entries: Sequence[Sequence[str]], whitelist_map: WhitelistMap, descent_path: str
        ) -> Any:
            return {entry[0]: entry[1] for entry in entries}

    @_whitelist_for_serdes(test_env, field_serializers={"entries": PairsSerializer})
    class Foo(NamedTuple):
        entries: Mapping[str, str]

    val = Foo({"a": "b", "c": "d"})
    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__class__": "Foo", "entries": [["a", "b"], ["c", "d"]]}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == val


def test_named_tuple_skip_when_empty_fields() -> None:
    test_map = WhitelistMap.create()

    # Separate scope since we redefine SameSnapshotTuple
    def get_orig_obj() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class SameSnapshotTuple(namedtuple("_Tuple", "foo")):
            def __new__(cls, foo):
                return super(SameSnapshotTuple, cls).__new__(cls, foo)

        return SameSnapshotTuple(foo="A")

    old_tuple = get_orig_obj()
    old_serialized = serialize_value(old_tuple, whitelist_map=test_map)
    old_snapshot = hash_str(old_serialized)

    # Separate scope since we redefine SameSnapshotTuple
    def get_new_obj_no_skip() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class SameSnapshotTuple(namedtuple("_SameSnapshotTuple", "foo bar")):
            def __new__(cls, foo, bar=None):
                return super(SameSnapshotTuple, cls).__new__(cls, foo, bar)

        return SameSnapshotTuple(foo="A")

    new_tuple_without_serializer = get_new_obj_no_skip()
    new_snapshot_without_serializer = hash_str(
        serialize_value(new_tuple_without_serializer, whitelist_map=test_map)
    )

    # Without setting skip_when_empty, the ID changes
    assert new_snapshot_without_serializer != old_snapshot

    # By setting `skip_when_empty_fields`, the ID stays the same as long as the new field is None

    @_whitelist_for_serdes(whitelist_map=test_map, skip_when_empty_fields={"bar"})
    class SameSnapshotTuple(namedtuple("_Tuple", "foo bar")):
        def __new__(cls, foo, bar=None):
            return super(SameSnapshotTuple, cls).__new__(cls, foo, bar)

    for bar_val in [None, [], {}, set()]:
        new_tuple = SameSnapshotTuple(foo="A", bar=bar_val)
        new_snapshot = hash_str(serialize_value(new_tuple, whitelist_map=test_map))

        assert old_snapshot == new_snapshot

        rehydrated_tuple = deserialize_value(
            old_serialized, SameSnapshotTuple, whitelist_map=test_map
        )
        assert rehydrated_tuple.foo == "A"
        assert rehydrated_tuple.bar is None

    new_tuple_with_bar = SameSnapshotTuple(foo="A", bar="B")
    assert new_tuple_with_bar.foo == "A"
    assert new_tuple_with_bar.bar == "B"


def test_named_tuple_custom_serializer():
    test_map = WhitelistMap.create()

    class FooSerializer(NamedTupleSerializer):
        def after_pack(self, **storage_dict: Dict[str, Any]):
            storage_dict["colour"] = storage_dict["color"]
            del storage_dict["color"]
            return storage_dict

        def before_unpack(self, **storage_dict: Dict[str, Any]):
            storage_dict["color"] = storage_dict["colour"]
            del storage_dict["colour"]
            return storage_dict

    @_whitelist_for_serdes(whitelist_map=test_map, serializer=FooSerializer)
    class Foo(NamedTuple):
        color: str

    val = Foo("red")
    serialized = serialize_value(val, whitelist_map=test_map)
    assert serialized == '{"__class__": "Foo", "colour": "red"}'
    deserialized = deserialize_value(serialized, whitelist_map=test_map)
    assert deserialized == val


def test_named_tuple_custom_serializer_error_handling():
    test_map = WhitelistMap.create()

    class FooSerializer(NamedTupleSerializer):
        def handle_unpack_error(self, exc: Exception, **storage_dict: Any) -> "Foo":
            return Foo("default")

    @_whitelist_for_serdes(whitelist_map=test_map, serializer=FooSerializer)
    class Foo(NamedTuple):
        color: str

    old_serialized = '{"__class__": "Foo", "colour": "red"}'
    deserialized = deserialize_value(old_serialized, whitelist_map=test_map)
    assert deserialized == Foo("default")

    # no custom error handling
    @_whitelist_for_serdes(whitelist_map=test_map)
    class Bar(NamedTuple):
        color: str

    with pytest.raises(Exception):
        old_serialized = '{"__class__": "Bar", "colour": "red"}'
        deserialized = deserialize_value(old_serialized, whitelist_map=test_map)


def test_long_int():
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class NumHolder(NamedTuple):
        num: int

    x = NumHolder(98765432109876543210)
    ser_x = serialize_value(x, test_map)
    roundtrip_x = deserialize_value(ser_x, whitelist_map=test_map)
    assert x.num == roundtrip_x.num


def test_enum_storage_name() -> None:
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env, storage_name="Bar")
    class Foo(Enum):
        RED = "color.red"

    val = Foo.RED

    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__enum__": "Bar.RED"}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == Foo.RED


def test_enum_old_storage_names() -> None:
    legacy_env = WhitelistMap.create()

    @_whitelist_for_serdes(legacy_env)
    class OldFoo(Enum):
        RED = "color.red"

    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env, old_storage_names={"OldFoo"})
    class Foo(Enum):
        RED = "color.red"

    serialized = serialize_value(Foo.RED, whitelist_map=test_env)
    assert serialized == '{"__enum__": "Foo.RED"}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == Foo.RED

    old_serialized = serialize_value(OldFoo.RED, whitelist_map=legacy_env)
    old_deserialized = deserialize_value(old_serialized, whitelist_map=test_env)
    assert old_deserialized == Foo.RED


def test_enum_custom_serializer():
    test_env = WhitelistMap.create()

    class MyEnumSerializer(EnumSerializer["Foo"]):
        def unpack(self, packed_val: str) -> "Foo":
            packed_val = packed_val.replace("BLUE", "RED")
            return Foo[packed_val]

        def pack(self, unpacked_val: "Foo", whitelist_map: WhitelistMap, descent_path: str) -> str:
            return f"Foo.{unpacked_val.name.replace('RED', 'BLUE')}"

    @_whitelist_for_serdes(test_env, serializer=MyEnumSerializer)
    class Foo(Enum):
        RED = "color.red"

    serialized = serialize_value(Foo.RED, whitelist_map=test_env)
    assert serialized == '{"__enum__": "Foo.BLUE"}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == Foo.RED
