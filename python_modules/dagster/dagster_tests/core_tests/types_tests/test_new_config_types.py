from dagster.core.types import Int, Nullable, List
from dagster.core.types.evaluator import validate_config
from dagster.core.types.field import resolve_to_config_type


def test_config_int():
    int_inst = resolve_to_config_type(Int)
    assert not validate_config(int_inst, 1)
    assert validate_config(int_inst, None)
    assert validate_config(int_inst, 'r')

    assert not int_inst.is_list
    assert not int_inst.is_nullable
    assert not (int_inst.is_nullable or int_inst.is_list)


def test_nullable_int():
    nullable_int_inst = resolve_to_config_type(Nullable(Int))
    assert not validate_config(nullable_int_inst, 1)
    assert not validate_config(nullable_int_inst, None)
    assert validate_config(nullable_int_inst, 'r')


def test_list_int():
    list_int = resolve_to_config_type(List(Int))
    assert not validate_config(list_int, [1])
    assert not validate_config(list_int, [1, 2])
    assert not validate_config(list_int, [])
    assert validate_config(list_int, [None])
    assert validate_config(list_int, [1, None])
    assert validate_config(list_int, None)
    assert validate_config(list_int, [1, 'absdf'])


def test_list_nullable_int():
    lni = resolve_to_config_type(List(Nullable(Int)))
    assert not validate_config(lni, [1])
    assert not validate_config(lni, [1, 2])
    assert not validate_config(lni, [])
    assert not validate_config(lni, [None])
    assert not validate_config(lni, [1, None])
    assert validate_config(lni, None)
    assert validate_config(lni, [1, 'absdf'])
