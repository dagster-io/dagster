import re
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest

from dagster import Failure, PipelineDefinition, String, TypeCheck, dagster_type
from dagster.core.errors import DagsterInvariantViolationError
from dagster.utils.temp_file import _unlink_swallow_errors
from dagster.utils.test import check_dagster_type, execute_solids_within_pipeline


def test_unlink_swallow_errors():
    _unlink_swallow_errors('32kjhb4kjsbfdkbf.jdfhks83')


def test_execute_isolated_solids_with_bad_solid_names():
    with pytest.raises(DagsterInvariantViolationError, match='but that solid was not found'):
        execute_solids_within_pipeline(PipelineDefinition([]), [], {'foo': {'bar': 'baz'}})


def test_check_dagster_type():
    res = check_dagster_type(Any, 'bar')
    assert res is None

    res = check_dagster_type(Any, None)
    assert res is None

    res = check_dagster_type(str, 'bar')
    assert res is None

    with pytest.raises(
        Failure, match=re.escape('Value "1" of python type "int" must be a string.')
    ):
        res = check_dagster_type(str, 1)

    res = check_dagster_type(String, 'bar')
    assert res is None

    res = check_dagster_type(list, ['foo', 'bar'])
    assert res is None

    res = check_dagster_type(List, ['foo', 'bar'])
    assert res is None

    res = check_dagster_type(List[Any], ['foo', 'bar'])
    assert res is None

    res = check_dagster_type(List[str], ['foo', 'bar'])
    assert res is None

    res = check_dagster_type(Any, {'foo': 'bar'})
    assert res is None

    res = check_dagster_type(dict, {'foo': 'bar'})
    assert res is None

    res = check_dagster_type(Dict, {'foo': 'bar'})
    assert res is None

    res = check_dagster_type(Dict[Any, Any], {'foo': 'bar'})
    assert res is None

    res = check_dagster_type(Dict[str, str], {'foo': 'bar'})
    assert res is None

    with pytest.raises(Failure, match=re.escape('Value "bar" of python type "str" must be a int.')):
        check_dagster_type(Dict[str, int], {'foo': 'bar'})

    res = check_dagster_type(tuple, ('foo', 'bar'))
    assert res is None

    res = check_dagster_type(Tuple, ('foo', 'bar'))
    assert res is None

    res = check_dagster_type(Tuple[Any, Any], ('foo', 'bar'))
    assert res is None

    res = check_dagster_type(Tuple[str, str], ('foo', 'bar'))
    assert res is None

    res = check_dagster_type(Tuple[str, str], ('foo', 'bar'))
    assert res is None

    with pytest.raises(
        Failure,
        match=re.escape(
            'Tuple with key TypedPythonTupleString.String requires 2 entries. Received tuple '
            'with 3 values'
        ),
    ):
        res = check_dagster_type(Tuple[str, str], ('foo', 'bar', 'baz'))

    res = check_dagster_type(Set, {'foo', 'bar'})
    assert res is None

    res = check_dagster_type(Set[Any], {'foo', 'bar'})
    assert res is None

    res = check_dagster_type(Set[str], {'foo', 'bar'})
    assert res is None

    with pytest.raises(Failure, match=re.escape('Value "foo" of python type "str" must be a int.')):
        res = check_dagster_type(Set[int], {'foo'})

    res = check_dagster_type(Optional[str], 'str')
    assert res is None

    res = check_dagster_type(Optional[str], None)
    assert res is None

    class Foo(object):
        pass

    class Bar(object):
        pass

    res = check_dagster_type(Foo, Foo())
    assert res is None

    with pytest.raises(
        Failure,
        match=re.escape('Value of type <class \'dagster_tests.utils_tests.test_test_utils')
        + '('
        + re.escape('.test_check_dagster_type.<locals>')
        + ')?'
        + re.escape(
            '.Bar\'> failed type check for Dagster type Implicit[Foo], expected value to be '
            'of Python type Foo.'
        ),
    ):
        res = check_dagster_type(Foo, Bar())

    @dagster_type
    class Baz(object):
        pass

    res = check_dagster_type(Baz, Baz())
    assert res is None

    @dagster_type(type_check=lambda _: None)
    class Quux(object):
        pass

    res = check_dagster_type(Quux, Quux())
    assert res is None

    def raise_failure(_):
        raise Failure('failed')

    @dagster_type(type_check=raise_failure)
    class Corge(object):
        pass

    with pytest.raises(Failure, match='failed'):
        res = check_dagster_type(Corge, Corge())

    @dagster_type(typecheck_metadata_fn=lambda _: TypeCheck('a_check', []))
    class Garble(object):
        pass

    res = check_dagster_type(Garble, Garble())
    assert isinstance(res, TypeCheck)
    assert res.description == 'a_check'
