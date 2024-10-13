import dataclasses
import re
import string
from collections import namedtuple
from enum import Enum
from typing import AbstractSet, Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Union

import dagster._check as check
import pydantic
import pytest
from dagster._model import DagsterModel
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes.errors import DeserializationError, SerdesUsageError, SerializationError
from dagster._serdes.serdes import (
    EnumSerializer,
    FieldSerializer,
    NamedTupleSerializer,
    SerializableNonScalarKeyMapping,
    SetToSequenceFieldSerializer,
    UnpackContext,
    WhitelistMap,
    _whitelist_for_serdes,
    deserialize_value,
    pack_value,
    serialize_value,
    unpack_value,
)
from dagster._serdes.utils import hash_str
from dagster._utils.cached_method import cached_method


def test_deserialize_value_ok():
    unpacked_tuple = deserialize_value('{"foo": "bar"}', as_type=dict)
    assert unpacked_tuple
    assert unpacked_tuple["foo"] == "bar"


def test_deserialize_json_non_namedtuple():
    with pytest.raises(DeserializationError, match="was not expected type"):
        deserialize_value('{"foo": "bar"}', NamedTuple)


@pytest.mark.parametrize("bad_obj", [1, None, False])
def test_deserialize_json_invalid_types(bad_obj):
    with pytest.raises(check.ParameterCheckError):
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
    val = {"a": {"b": [{}, {}, {"c": Fizz(1)}]}}
    packed = pack_value(val, whitelist_map=test_map)
    ser = serialize_value(val, whitelist_map=test_map)

    # when parsing from serialized - we unpack objects bottom-up in instead of so have no path
    with pytest.raises(
        DeserializationError,
        match='Attempted to deserialize class "Fizz" which is not in the whitelist',
    ):
        unpack_value(packed, whitelist_map=blank_map)

    with pytest.raises(
        DeserializationError,
        match='Attempted to deserialize class "Fizz" which is not in the whitelist',
    ):
        deserialize_value(ser, whitelist_map=blank_map)


def test_forward_compat_serdes_new_field_with_default() -> None:
    test_map = WhitelistMap.create()

    # Separate scope since we redefine Quux
    def get_orig_obj() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class Quux(NamedTuple("_Quux", [("foo", str), ("bar", str)])):
            def __new__(cls, foo, bar):
                return super(Quux, cls).__new__(cls, foo, bar)

        assert "Quux" in test_map.object_serializers
        serializer = test_map.object_serializers["Quux"]
        assert serializer.klass is Quux
        return Quux("zip", "zow")

    orig = get_orig_obj()
    serialized = serialize_value(orig, whitelist_map=test_map)

    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Quux(NamedTuple("_Quux", [("foo", str), ("bar", str), ("baz", Optional[str])])):
        def __new__(cls, foo, bar, baz=None):
            return super(Quux, cls).__new__(cls, foo, bar, baz=baz)

    assert "Quux" in test_map.object_serializers
    serializer_v2 = test_map.object_serializers["Quux"]
    assert serializer_v2.klass is Quux

    deserialized = deserialize_value(serialized, as_type=Quux, whitelist_map=test_map)

    assert deserialized != orig
    assert deserialized.foo == orig.foo
    assert deserialized.bar == orig.bar
    assert deserialized.baz is None


def test_forward_compat_serdes_new_enum_field() -> None:
    test_map = WhitelistMap.create()

    # Separate scope since we redefine Corge
    def get_orig_obj() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class Corge(Enum):
            FOO = 1
            BAR = 2

        assert "Corge" in test_map.enum_serializers
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


def test_serdes_enum_backcompat() -> None:
    test_map = WhitelistMap.create()

    # Separate scope since we redefine Corge
    def get_orig_obj() -> Any:
        @_whitelist_for_serdes(whitelist_map=test_map)
        class Corge(Enum):
            FOO = 1
            BAR = 2

        assert "Corge" in test_map.enum_serializers
        return Corge.FOO

    corge = get_orig_obj()
    serialized = serialize_value(corge, whitelist_map=test_map)

    class CorgeBackCompatSerializer(EnumSerializer):
        def unpack(self, value):
            if value == "FOO":
                value = "FOO_FOO"

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

    test_map = WhitelistMap.create()

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
        class Quux(NamedTuple):
            bar: str
            baz: str

        return Quux

    orig_klass = register_orig()

    # new version has a new field with a new type
    new_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=new_map)
    class Quux(NamedTuple):
        foo: "Foo"
        bar: str
        baz: str
        buried: dict

    @_whitelist_for_serdes(whitelist_map=new_map)
    class Foo(NamedTuple):
        s: str

    new_quux = Quux(
        foo=Foo("wow"),
        bar="bar",
        baz="baz",
        buried={
            "top": Foo("d"),
            "list": [Foo("l"), 2, 3],
            "set": {Foo("s"), 2, 3},
            "frozenset": frozenset((1, 2, Foo("fs"))),
            "deep": {"1": [{"2": {"3": [Foo("d")]}}]},
        },
    )

    # write from new
    serialized = serialize_value(new_quux, whitelist_map=new_map)

    # read from old, Foo ignored
    deserialized = deserialize_value(serialized, as_type=orig_klass, whitelist_map=old_map)
    assert deserialized.bar == "bar"
    assert deserialized.baz == "baz"


def test_error_on_multiple_deserializers() -> None:
    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map)
    class Foo(NamedTuple):
        x: int

    with pytest.raises(
        SerdesUsageError, match="Multiple deserializers registered for storage name `Foo`"
    ):

        @_whitelist_for_serdes(whitelist_map=test_map, storage_name="Foo")
        class Foo2(NamedTuple):
            x: int
            y: str


def serdes_test_class(klass):
    test_map = WhitelistMap.create()

    return _whitelist_for_serdes(whitelist_map=test_map)(klass)


def test_wrong_first_arg():
    with pytest.raises(SerdesUsageError) as exc_info:

        @serdes_test_class
        class NotCls(namedtuple("NotCls", "field_one field_two")):
            def __new__(not_cls, field_two, field_one):  # type: ignore
                return super(NotCls, not_cls).__new__(field_one, field_two)

    assert str(exc_info.value) == 'For NotCls: First parameter must be _cls or cls. Got "not_cls".'


def test_incorrect_order():
    with pytest.raises(SerdesUsageError) as exc_info:

        @serdes_test_class
        class WrongOrder(namedtuple("WrongOrder", "field_one field_two")):
            def __new__(cls, field_two, field_one):
                return super(WrongOrder, cls).__new__(field_one, field_two)

    assert (
        str(exc_info.value) == "For WrongOrder: "
        "Params to __new__ must match the order of field declaration "
        "for NamedTuples that are not @record based. Declared field number 1 in the namedtuple "
        'is "field_one". Parameter 1 in __new__ method is "field_two".'
    )


def test_missing_one_parameter():
    with pytest.raises(SerdesUsageError) as exc_info:

        @serdes_test_class
        class MissingFieldInNew(namedtuple("MissingFieldInNew", "field_one field_two field_three")):
            def __new__(cls, field_one, field_two):
                return super(MissingFieldInNew, cls).__new__(field_one, field_two, None)

    assert (
        str(exc_info.value) == "For MissingFieldInNew: "
        "Missing parameters to __new__. You have declared fields "
        "that are not present as parameters to the "
        "to the __new__ method. In order for both serdes serialization "
        "and pickling to work, these must match or kwargs and kwargs_fields must be used. "
        "Missing: ['field_three']"
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
        str(exc_info.value) == "For MissingFieldsInNew: "
        "Missing parameters to __new__. You have declared fields "
        "that are not present as parameters to the "
        "to the __new__ method. In order for both serdes serialization "
        "and pickling to work, these must match or kwargs and kwargs_fields must be used. "
        "Missing: ['field_three', 'field_four']"
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
        str(exc_info.value) == "For OldFieldsWithoutDefaults: "
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
            check.set_param(reg_set, "reg_set")
            check.inst_param(frozen_set, "frozen_set", frozenset)
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


# Ensures it is possible to simultaneously have a class Foo and a separate class that serializes to
# Foo, if Foo has a different storage name.
def test_named_tuple_storage_name() -> None:
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env, storage_name="Bar")
    class Foo(NamedTuple):
        color: str

    @_whitelist_for_serdes(test_env, storage_name="Foo")
    class Bar(NamedTuple):
        shape: str

    val = Foo("red")
    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__class__": "Bar", "color": "red"}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == val

    val = Bar("square")
    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__class__": "Foo", "shape": "square"}'
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
            self,
            entries: Mapping[str, str],
            whitelist_map: WhitelistMap,
            descent_path: str,
        ) -> Sequence[Sequence[str]]:
            return list(entries.items())

        def unpack(
            self,
            entries: Sequence[Sequence[str]],
            whitelist_map: WhitelistMap,
            context: UnpackContext,
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


def test_set_to_sequence_field_serializer() -> None:
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env, field_serializers={"colors": SetToSequenceFieldSerializer})
    class Foo(NamedTuple):
        colors: AbstractSet[str]

    val = Foo({"red", "green"})
    serialized = serialize_value(val, whitelist_map=test_env)
    assert serialized == '{"__class__": "Foo", "colors": ["green", "red"]}'
    deserialized = deserialize_value(serialized, whitelist_map=test_env)
    assert deserialized == val


def test_named_tuple_invalid_ignored_values() -> None:
    def get_serialized_future() -> str:
        future_map = WhitelistMap.create()

        @_whitelist_for_serdes(whitelist_map=future_map)
        class A(NamedTuple):
            x: int
            future_field: "Future1"

        @_whitelist_for_serdes(whitelist_map=future_map)
        class Future1(NamedTuple):
            val: int
            inner1: Optional["Future1"]
            inner2: "Future2"

        @_whitelist_for_serdes(whitelist_map=future_map)
        class Future2(NamedTuple):
            val: str

        future_object = A(0, Future1(1, Future1(2, None, Future2("b")), Future2("a")))
        return serialize_value(future_object, whitelist_map=future_map)

    current_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=current_map)
    class A(NamedTuple):
        x: int

    assert deserialize_value(get_serialized_future(), as_type=A, whitelist_map=current_map) == A(0)


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
    test_map = WhitelistMap.create()

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

    test_map = WhitelistMap.create()

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


def test_named_tuple_skip_when_none_fields() -> None:
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
    test_map = WhitelistMap.create()

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

    # Without setting skip_when_none, the ID changes
    assert new_snapshot_without_serializer != old_snapshot

    # By setting `skip_when_none_fields`, the ID stays the same as long as the new field is None

    test_map = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_map, skip_when_none_fields={"bar"})
    class SameSnapshotTuple(namedtuple("_Tuple", "foo bar")):
        def __new__(cls, foo, bar=None):
            return super(SameSnapshotTuple, cls).__new__(cls, foo, bar)

    for bar_val in [None, [], {}, set()]:
        new_tuple = SameSnapshotTuple(foo="A", bar=bar_val)
        new_snapshot = hash_str(serialize_value(new_tuple, whitelist_map=test_map))

        # Only None is dropped, not empty collections
        if bar_val is None:
            assert old_snapshot == new_snapshot
        else:
            assert old_snapshot != new_snapshot

    rehydrated_tuple = deserialize_value(old_serialized, SameSnapshotTuple, whitelist_map=test_map)
    assert rehydrated_tuple.foo == "A"
    assert rehydrated_tuple.bar is None

    new_tuple_with_bar = SameSnapshotTuple(foo="A", bar="B")
    assert new_tuple_with_bar.foo == "A"
    assert new_tuple_with_bar.bar == "B"


def test_named_tuple_custom_serializer():
    test_map = WhitelistMap.create()

    class FooSerializer(NamedTupleSerializer):
        def pack_items(self, *args, **kwargs):
            for k, v in super().pack_items(*args, **kwargs):
                if k == "color":
                    yield "colour", v
                else:
                    yield k, v

        def before_unpack(self, context, unpacked_dict: Dict[str, Any]):
            unpacked_dict["color"] = unpacked_dict["colour"]
            del unpacked_dict["colour"]
            return unpacked_dict

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
        def handle_unpack_error(self, exc: Exception, context, storage_dict: Any) -> "Foo":
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


def test_serialize_non_scalar_key_mapping():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(whitelist_map=test_env)
    class Bar(NamedTuple):
        color: str

    non_scalar_key_mapping = SerializableNonScalarKeyMapping({Bar("red"): 1})

    serialized = serialize_value(non_scalar_key_mapping, whitelist_map=test_env)
    assert serialized == """{"__mapping_items__": [[{"__class__": "Bar", "color": "red"}, 1]]}"""
    assert non_scalar_key_mapping == deserialize_value(serialized, whitelist_map=test_env)


def test_serializable_non_scalar_key_mapping():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    class Bar(NamedTuple):
        color: str

    non_scalar_key_mapping = SerializableNonScalarKeyMapping({Bar("red"): 1})

    assert len(non_scalar_key_mapping) == 1
    assert non_scalar_key_mapping[Bar("red")] == 1
    assert list(iter(non_scalar_key_mapping)) == list(iter([Bar("red")]))

    with pytest.raises(NotImplementedError, match="SerializableNonScalarKeyMapping is immutable"):
        non_scalar_key_mapping["foo"] = None


def test_serializable_non_scalar_key_mapping_in_named_tuple():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    class Bar(NamedTuple):
        color: str

    @_whitelist_for_serdes(test_env)
    class Foo(NamedTuple("_Foo", [("keyed_by_non_scalar", Mapping[Bar, int])])):
        def __new__(cls, keyed_by_non_scalar):
            return super(Foo, cls).__new__(
                cls, SerializableNonScalarKeyMapping(keyed_by_non_scalar)
            )

    named_tuple = Foo(keyed_by_non_scalar={Bar("red"): 1})
    assert (
        deserialize_value(
            serialize_value(named_tuple, whitelist_map=test_env), whitelist_map=test_env
        )
        == named_tuple
    )


def test_objects():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    class SomeNT(NamedTuple):
        nums: List[int]

    @_whitelist_for_serdes(test_env)
    @dataclasses.dataclass
    class InnerDataclass:
        f: float

    @_whitelist_for_serdes(test_env)
    class SomeModel(pydantic.BaseModel):
        id: int
        name: str

    @_whitelist_for_serdes(test_env)
    class SomeDagsterModel(DagsterModel):
        id: int
        name: str

    @_whitelist_for_serdes(test_env)
    @pydantic.dataclasses.dataclass
    class DataclassObj:
        s: str
        i: int
        d: InnerDataclass
        nt: SomeNT
        m: SomeModel
        st: SomeDagsterModel

    o = DataclassObj(
        "woo",
        4,
        InnerDataclass(1.2),
        SomeNT([1, 2, 3]),
        SomeModel(id=4, name="zuck"),
        SomeDagsterModel(id=4, name="zuck"),
    )
    ser_o = serialize_value(o, whitelist_map=test_env)
    assert deserialize_value(ser_o, whitelist_map=test_env) == o

    packed_o = pack_value(o, whitelist_map=test_env)
    assert unpack_value(packed_o, whitelist_map=test_env, as_type=DataclassObj) == o


def test_object_migration():
    nt_env = WhitelistMap.create()

    @_whitelist_for_serdes(nt_env)
    class MyEnt(NamedTuple):  # type: ignore
        name: str
        age: int
        children: List["MyEnt"]

    nt_ent = MyEnt("dad", 40, [MyEnt("sis", 4, [])])
    ser_nt_ent = serialize_value(nt_ent, whitelist_map=nt_env)
    assert deserialize_value(ser_nt_ent, whitelist_map=nt_env) == nt_ent

    py_dc_env = WhitelistMap.create()

    @_whitelist_for_serdes(py_dc_env)
    @pydantic.dataclasses.dataclass
    class MyEnt:  # type: ignore
        name: str
        age: int
        children: List["MyEnt"]

    # can deserialize previous NamedTuples in to future dataclasses
    py_dc_ent = deserialize_value(ser_nt_ent, whitelist_map=py_dc_env)
    assert py_dc_ent

    py_m_env = WhitelistMap.create()

    @_whitelist_for_serdes(py_m_env)
    class MyEnt(pydantic.BaseModel):
        name: str
        age: int
        children: List["MyEnt"]

    # can deserialize previous NamedTuples in to future pydantic models
    py_dc_ent = deserialize_value(ser_nt_ent, whitelist_map=py_m_env)
    assert py_dc_ent


def test_record() -> None:
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    @record
    class MyModel:
        nums: List[int]

    m = MyModel(nums=[1, 2, 3])
    m_str = serialize_value(m, whitelist_map=test_env)
    assert m == deserialize_value(m_str, whitelist_map=test_env)

    @_whitelist_for_serdes(test_env)
    @record(checked=False)
    class UncheckedModel:
        nums: List[int]
        optional: int = 130

    m = UncheckedModel(nums=[1, 2, 3])
    m_str = serialize_value(m, whitelist_map=test_env)
    assert m == deserialize_value(m_str, whitelist_map=test_env)

    @_whitelist_for_serdes(test_env)
    @record
    class CachedModel:
        nums: List[int]
        optional: int = 42

        @cached_method
        def map(self) -> dict:
            return {str(v): v for v in self.nums}

    m = CachedModel(nums=[1, 2, 3])
    m_map = m.map()
    assert m_map is m.map()
    m_str = serialize_value(m, whitelist_map=test_env)
    m_2 = deserialize_value(m_str, whitelist_map=test_env)

    assert m == m_2

    @_whitelist_for_serdes(test_env)
    @record_custom
    class LegacyModel(IHaveNew):
        nums: List[int]

        def __new__(cls, nums: Optional[List[int]] = None, old_nums: Optional[List[int]] = None):
            return super().__new__(
                cls,
                nums=nums or old_nums,
            )

    m = LegacyModel(nums=[1, 2, 3])

    m_str = serialize_value(m, whitelist_map=test_env)
    m2_str = m_str.replace("nums", "old_nums")
    assert m == deserialize_value(m2_str, whitelist_map=test_env)


def test_record_fwd_ref():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    @record
    class MyModel:
        foos: List["Foo"]

    @_whitelist_for_serdes(test_env)
    @record
    class Foo:
        age: int

    def _out_of_scope():
        # cant find "Foo" in definition or callsite captured scopes
        # requires serdes to set contextual namespace
        return deserialize_value(
            '{"__class__": "MyModel", "foos": [{"__class__": "Foo", "age": 6}]}',
            MyModel,
            whitelist_map=test_env,
        )

    assert _out_of_scope()


def test_record_subclass() -> None:
    test_env = WhitelistMap.create()

    @record
    class MyRecord:
        name: str

    @_whitelist_for_serdes(test_env)
    class Child(MyRecord): ...

    c = Child(name="kiddo")
    r_str = serialize_value(c, whitelist_map=test_env)
    assert deserialize_value(r_str, whitelist_map=test_env) == c


def test_record_kwargs():
    test_env = WhitelistMap.create()

    with pytest.raises(
        SerdesUsageError,
        match="Params to __new__ must match the order of field declaration for NamedTuples that are not @record based",
    ):

        @_whitelist_for_serdes(test_env, kwargs_fields={"name", "stuff"})
        class _(NamedTuple("_", [("name", str), ("stuff", List[Any])])):
            def __new__(cls, **kwargs): ...

    with pytest.raises(
        SerdesUsageError,
        match="kwargs capture used in __new__ but kwargs_fields was not specified",
    ):

        @_whitelist_for_serdes(test_env)
        @record_custom
        class _:
            name: str
            stuff: List[Any]

            def __new__(cls, **kwargs): ...

    with pytest.raises(
        SerdesUsageError,
        match='Expected field "stuff" in kwargs_fields but it was not specified',
    ):

        @_whitelist_for_serdes(test_env, kwargs_fields={"name"})
        @record_custom
        class _:
            name: str
            stuff: List[Any]

            def __new__(cls, **kwargs): ...

    @_whitelist_for_serdes(test_env, kwargs_fields={"name", "stuff"})
    @record_custom
    class MyRecord:
        name: str
        stuff: List[Any]

        def __new__(cls, **kwargs):
            return super().__new__(
                cls,
                name=kwargs.get("name", ""),
                stuff=kwargs.get("stuff", []),
            )

    r = MyRecord()
    assert r
    assert (
        deserialize_value(serialize_value(r, whitelist_map=test_env), whitelist_map=test_env) == r
    )
    r = MyRecord(name="CUSTOM", stuff=[1, 2, 3, 4, 5, 6])
    assert r
    assert (
        deserialize_value(serialize_value(r, whitelist_map=test_env), whitelist_map=test_env) == r
    )


def test_record_remap() -> None:
    test_env = WhitelistMap.create()

    # time 1: record object created with non-serializable field

    class Complex:
        def __init__(self, s: str):
            self.s = s

    @record
    class Record_T1:
        foo: Complex

    assert Record_T1(foo=Complex("old"))

    # time 2: record updated to serdes, to maintain API we use remapping

    @_whitelist_for_serdes(test_env)
    @record_custom(field_to_new_mapping={"foo_str": "foo"})
    class Record_T2(IHaveNew):
        foo_str: str

        def __new__(cls, foo: Union[Complex, str]):
            if isinstance(foo, Complex):
                foo = foo.s

            return super().__new__(
                cls,
                foo_str=foo,
            )

        @property
        def foo(self):
            return Complex(self.foo_str)

    r = Record_T2(foo=Complex("old"))
    assert r
    assert (
        deserialize_value(serialize_value(r, whitelist_map=test_env), whitelist_map=test_env) == r
    )
