from dagster import Array, Int, Noneable
from dagster.config.config_type import ConfigTypeKind
from dagster.config.field import resolve_to_config_type
from dagster.config.validate import validate_config


def test_config_any():
    any_inst = resolve_to_config_type(None)
    assert validate_config(any_inst, 1).success
    assert validate_config(any_inst, None).success
    assert validate_config(any_inst, "r").success
    assert any_inst.kind == ConfigTypeKind.ANY


def test_config_int():
    int_inst = resolve_to_config_type(Int)
    assert validate_config(int_inst, 1).success
    assert not validate_config(int_inst, None).success
    assert not validate_config(int_inst, "r").success
    assert int_inst.kind == ConfigTypeKind.SCALAR


def test_optional_int():
    optional_int_inst = resolve_to_config_type(Noneable(int))

    assert validate_config(optional_int_inst, 1).success
    assert validate_config(optional_int_inst, None).success
    assert not validate_config(optional_int_inst, "r").success


def test_list_int():
    list_int = resolve_to_config_type([Int])

    assert validate_config(list_int, [1]).success
    assert validate_config(list_int, [1, 2]).success
    assert validate_config(list_int, []).success
    assert not validate_config(list_int, [None]).success
    assert not validate_config(list_int, [1, None]).success
    assert not validate_config(list_int, None).success
    assert not validate_config(list_int, [1, "absdf"]).success


def test_list_nullable_int():
    lni = resolve_to_config_type(Array(Noneable(int)))

    assert validate_config(lni, [1]).success
    assert validate_config(lni, [1, 2]).success
    assert validate_config(lni, []).success
    assert validate_config(lni, [None]).success
    assert validate_config(lni, [1, None]).success
    assert not validate_config(lni, None).success
    assert not validate_config(lni, [1, "absdf"]).success


def test_map_int():
    map_str_int = resolve_to_config_type({str: Int})

    assert validate_config(map_str_int, {"a": 1}).success
    assert validate_config(map_str_int, {"a": 1, "b": 2}).success
    assert validate_config(map_str_int, {}).success
    assert not validate_config(map_str_int, {"a": None}).success
    assert not validate_config(map_str_int, {"a": 1, "b": None}).success
    assert not validate_config(map_str_int, None).success
    assert not validate_config(map_str_int, {"a": 1, "b": "absdf"}).success
    assert not validate_config(map_str_int, {"a": 1, 4: 4}).success
    assert not validate_config(map_str_int, {"a": 1, None: 4}).success

    map_int_int = resolve_to_config_type({Int: Int})

    assert validate_config(map_int_int, {1: 1}).success
    assert validate_config(map_int_int, {2: 1, 3: 2}).success
    assert validate_config(map_int_int, {}).success
    assert not validate_config(map_int_int, {1: None}).success
    assert not validate_config(map_int_int, {1: 1, 2: None}).success
    assert not validate_config(map_int_int, None).success
    assert not validate_config(map_int_int, {1: 1, 2: "absdf"}).success
    assert not validate_config(map_int_int, {4: 1, "a": 4}).success
    assert not validate_config(map_int_int, {5: 1, None: 4}).success
