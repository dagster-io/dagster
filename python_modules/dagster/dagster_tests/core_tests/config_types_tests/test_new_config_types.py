from dagster.core.types import Int, List, Optional
from dagster.core.types.config.evaluator.validate import validate_config
from dagster.core.types.config.field import resolve_to_config_type


def test_config_any():
    any_inst = resolve_to_config_type(None)
    assert validate_config(any_inst, 1).success
    assert validate_config(any_inst, None).success
    assert validate_config(any_inst, 'r').success
    assert not any_inst.is_list
    assert not any_inst.is_nullable
    assert any_inst.is_any


def test_config_int():
    int_inst = resolve_to_config_type(Int)
    assert validate_config(int_inst, 1).success
    assert not validate_config(int_inst, None).success
    assert not validate_config(int_inst, 'r').success
    assert not int_inst.is_list
    assert not int_inst.is_nullable
    assert not (int_inst.is_nullable or int_inst.is_list)


def test_optional_int():
    optional_int_inst = resolve_to_config_type(Optional[Int])

    assert validate_config(optional_int_inst, 1).success
    assert validate_config(optional_int_inst, None).success
    assert not validate_config(optional_int_inst, 'r').success


def test_list_int():
    list_int = resolve_to_config_type(List[Int])

    assert validate_config(list_int, [1]).success
    assert validate_config(list_int, [1, 2]).success
    assert validate_config(list_int, []).success
    assert not validate_config(list_int, [None]).success
    assert not validate_config(list_int, [1, None]).success
    assert not validate_config(list_int, None).success
    assert not validate_config(list_int, [1, 'absdf']).success


def test_list_nullable_int():
    lni = resolve_to_config_type(List[Optional[Int]])

    assert validate_config(lni, [1]).success
    assert validate_config(lni, [1, 2]).success
    assert validate_config(lni, []).success
    assert validate_config(lni, [None]).success
    assert validate_config(lni, [1, None]).success
    assert not validate_config(lni, None).success
    assert not validate_config(lni, [1, 'absdf']).success
