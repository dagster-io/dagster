from dagster.core.types import Int, Optional, List
from dagster.core.types.evaluator import evaluate_config
from dagster.core.types.field import resolve_to_config_type


def test_config_int():
    int_inst = resolve_to_config_type(Int)
    assert evaluate_config(int_inst, 1).success
    assert not evaluate_config(int_inst, None).success
    assert not evaluate_config(int_inst, 'r').success
    assert not int_inst.is_list
    assert not int_inst.is_nullable
    assert not (int_inst.is_nullable or int_inst.is_list)


def test_optional_int():
    optional_int_inst = resolve_to_config_type(Optional[Int])

    assert evaluate_config(optional_int_inst, 1).success
    assert evaluate_config(optional_int_inst, None).success
    assert not evaluate_config(optional_int_inst, 'r').success


def test_list_int():
    list_int = resolve_to_config_type(List[Int])

    assert evaluate_config(list_int, [1]).success
    assert evaluate_config(list_int, [1, 2]).success
    assert evaluate_config(list_int, []).success
    assert not evaluate_config(list_int, [None]).success
    assert not evaluate_config(list_int, [1, None]).success
    assert not evaluate_config(list_int, None).success
    assert not evaluate_config(list_int, [1, 'absdf']).success


def test_list_nullable_int():
    lni = resolve_to_config_type(List[Optional[Int]])

    assert evaluate_config(lni, [1]).success
    assert evaluate_config(lni, [1, 2]).success
    assert evaluate_config(lni, []).success
    assert evaluate_config(lni, [None]).success
    assert evaluate_config(lni, [1, None]).success
    assert not evaluate_config(lni, None).success
    assert not evaluate_config(lni, [1, 'absdf']).success
