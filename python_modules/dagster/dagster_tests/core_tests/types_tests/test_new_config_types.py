from dagster.core.types import Int, Optional, List
from dagster.core.types.evaluator import evaluate_config
from dagster.core.types.field import resolve_to_config_type


def test_config_int():
    int_inst = resolve_to_config_type(Int)
    errors, _ = evaluate_config(int_inst, 1)
    assert not errors

    errors, _ = evaluate_config(int_inst, None)
    assert errors

    errors, _ = evaluate_config(int_inst, 'r')
    assert errors

    assert not int_inst.is_list
    assert not int_inst.is_nullable
    assert not (int_inst.is_nullable or int_inst.is_list)


def test_optional_int():
    optional_int_inst = resolve_to_config_type(Optional[Int])

    errors, _ = evaluate_config(optional_int_inst, 1)
    assert not errors

    errors, _ = evaluate_config(optional_int_inst, None)
    assert not errors

    errors, _ = evaluate_config(optional_int_inst, 'r')
    assert errors


def test_list_int():
    list_int = resolve_to_config_type(List[Int])

    errors, _ = evaluate_config(list_int, [1])
    assert not errors

    errors, _ = evaluate_config(list_int, [1, 2])
    assert not errors

    errors, _ = evaluate_config(list_int, [])
    assert not errors

    errors, _ = evaluate_config(list_int, [None])
    assert errors

    errors, _ = evaluate_config(list_int, [1, None])
    assert errors

    errors, _ = evaluate_config(list_int, None)
    assert errors

    errors, _ = evaluate_config(list_int, [1, 'absdf'])


def test_list_nullable_int():
    lni = resolve_to_config_type(List[Optional[Int]])

    errors, _ = evaluate_config(lni, [1])
    assert not errors

    errors, _ = evaluate_config(lni, [1, 2])
    assert not errors

    errors, _ = evaluate_config(lni, [])
    assert not errors

    errors, _ = evaluate_config(lni, [None])
    assert not errors

    errors, _ = evaluate_config(lni, [1, None])
    assert not errors

    errors, _ = evaluate_config(lni, None)
    assert errors

    errors, _ = evaluate_config(lni, [1, 'absdf'])
    assert errors
