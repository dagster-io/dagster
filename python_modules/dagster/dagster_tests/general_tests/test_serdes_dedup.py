from dagster._record import record
from dagster_shared.serdes.serdes import WhitelistMap, _whitelist_for_serdes, serialize_value
from dagster_shared.serdes.serdes_dedup import (
    PackedObjects,
    SerializationPackingContext,
    deserialize_value_with_packing,
    serialize_value_with_packing,
)


def test_nested_duplication_unhashable():
    test_map = WhitelistMap.create()
    _whitelist_for_serdes(whitelist_map=test_map)(PackedObjects)
    _whitelist_for_serdes(whitelist_map=test_map)(SerializationPackingContext)

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Foo:
        name: str
        val: int

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class FooHolder:
        foo_list: list[Foo]
        foo_dict: dict[str, Foo]

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class FooHolderHolder:
        foo_holders: list[FooHolder]

    a = Foo(name="a", val=1)
    b = Foo(name="b", val=2)

    a_holder = FooHolder(
        foo_list=[a, a, a, b],
        foo_dict={"a1": a, "a2": a, "a3": a, "b1": b},
    )
    b_holder = FooHolder(
        foo_list=[b, b, b, a],
        foo_dict={"b1": b, "b2": b, "b3": b, "a1": a},
    )

    final = FooHolderHolder(foo_holders=[a_holder, a_holder, b_holder])

    serialized = serialize_value_with_packing(final, whitelist_map=test_map)
    assert len(serialized) < len(serialize_value(final, whitelist_map=test_map))
    deserialized = deserialize_value_with_packing(serialized, whitelist_map=test_map)

    assert deserialized == final


def test_nested_duplication_hashable():
    test_map = WhitelistMap.create()
    _whitelist_for_serdes(whitelist_map=test_map)(PackedObjects)
    _whitelist_for_serdes(whitelist_map=test_map)(SerializationPackingContext)

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class Foo:
        name: str
        val: int

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class FooHolder:
        foo_1: Foo
        foo_2: Foo
        foo_3: Foo

    @_whitelist_for_serdes(whitelist_map=test_map)
    @record
    class FooHolderHolder:
        foo_holder_1: FooHolder
        foo_holder_2: FooHolder

    a = Foo(name="a", val=1)
    b = Foo(name="b", val=2)

    a_holder = FooHolder(
        foo_1=a,
        foo_2=a,
        foo_3=a,
    )
    b_holder = FooHolder(
        foo_1=b,
        foo_2=b,
        foo_3=b,
    )

    top_level = FooHolderHolder(foo_holder_1=a_holder, foo_holder_2=b_holder)
    final = [top_level, top_level, top_level, top_level, top_level, top_level, {"foo": top_level}]

    serialized = serialize_value_with_packing(final, whitelist_map=test_map)
    assert len(serialized) < len(serialize_value(final, whitelist_map=test_map))
    deserialized = deserialize_value_with_packing(serialized, whitelist_map=test_map)

    assert deserialized == final
