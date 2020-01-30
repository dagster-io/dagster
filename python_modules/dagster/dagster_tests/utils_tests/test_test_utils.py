import typing

import pytest

from dagster import (
    Any,
    Dict,
    List,
    Optional,
    PipelineDefinition,
    Set,
    String,
    Tuple,
    usable_as_dagster_type,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.utils.temp_file import _unlink_swallow_errors
from dagster.utils.test import check_dagster_type, execute_solids_within_pipeline


def test_unlink_swallow_errors():
    _unlink_swallow_errors('32kjhb4kjsbfdkbf.jdfhks83')


def test_execute_isolated_solids_with_bad_solid_names():
    with pytest.raises(DagsterInvariantViolationError, match='but that solid was not found'):
        execute_solids_within_pipeline(PipelineDefinition([]), [], {'foo': {'bar': 'baz'}})


def test_typing_invalid():

    for ttype in [
        typing.List,
        typing.List[str],
        typing.Optional[int],
        typing.Set,
        typing.Set[int],
        typing.Dict,
        typing.Dict[int, str],
        typing.Tuple,
        typing.Tuple[int, int],
    ]:
        with pytest.raises(DagsterInvariantViolationError):
            check_dagster_type(ttype, None)


def test_check_dagster_type():
    res = check_dagster_type(Any, 'bar')
    assert res.success

    res = check_dagster_type(Any, None)
    assert res.success

    res = check_dagster_type(str, 'bar')
    assert res.success

    res = check_dagster_type(str, 1)
    assert not res.success
    assert 'Value "1" of python type "int" must be a string.' in res.description

    res = check_dagster_type(String, 'bar')
    assert res.success

    res = check_dagster_type(list, ['foo', 'bar'])
    assert res.success

    res = check_dagster_type(List, ['foo', 'bar'])
    assert res.success

    res = check_dagster_type(List[Any], ['foo', 'bar'])
    assert res.success

    res = check_dagster_type(List[str], ['foo', 'bar'])
    assert res.success

    res = check_dagster_type(Any, {'foo': 'bar'})
    assert res.success

    res = check_dagster_type(dict, {'foo': 'bar'})
    assert res.success

    res = check_dagster_type(Dict, {'foo': 'bar'})
    assert res.success

    res = check_dagster_type(Dict[Any, Any], {'foo': 'bar'})
    assert res.success

    res = check_dagster_type(Dict[str, str], {'foo': 'bar'})
    assert res.success

    res = check_dagster_type(Dict[str, int], {'foo': 'bar'})
    assert not res.success
    assert 'Value "bar" of python type "str" must be a int.' in res.description

    res = check_dagster_type(tuple, ('foo', 'bar'))
    assert res.success

    res = check_dagster_type(Tuple, ('foo', 'bar'))
    assert res.success

    res = check_dagster_type(Tuple[Any, Any], ('foo', 'bar'))
    assert res.success

    res = check_dagster_type(Tuple[str, str], ('foo', 'bar'))
    assert res.success

    res = check_dagster_type(Tuple[str, str], ('foo', 'bar'))
    assert res.success

    res = check_dagster_type(Tuple[str, str], ('foo', 'bar', 'baz'))
    assert not res.success
    assert (
        'Tuple with key TypedPythonTupleString.String requires 2 entries, received 3 values'
    ) in res.description

    res = check_dagster_type(Set, {'foo', 'bar'})
    assert res.success

    res = check_dagster_type(Set[Any], {'foo', 'bar'})
    assert res.success

    res = check_dagster_type(Set[str], {'foo', 'bar'})
    assert res.success

    res = check_dagster_type(Set[int], {'foo'})
    assert not res.success
    assert 'Value "foo" of python type "str" must be a int.' in res.description

    res = check_dagster_type(Optional[str], 'str')
    assert res.success

    res = check_dagster_type(Optional[str], None)
    assert res.success

    @usable_as_dagster_type
    class Baz(object):
        pass

    res = check_dagster_type(Baz, Baz())
    assert res.success
