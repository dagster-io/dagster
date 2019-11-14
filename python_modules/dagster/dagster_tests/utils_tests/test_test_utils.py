import re
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest

from dagster import PipelineDefinition, String, TypeCheck, dagster_type
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

    class Foo(object):
        pass

    class Bar(object):
        pass

    res = check_dagster_type(Foo, Foo())
    assert res.success

    res = check_dagster_type(Foo, Bar())
    assert not res.success
    assert re.match(
        re.escape('Value of type <class \'dagster_tests.utils_tests.test_test_utils')
        + '('
        + re.escape('.test_check_dagster_type.<locals>')
        + ')?'
        + re.escape(
            '.Bar\'> failed type check for Dagster type Implicit[Foo], expected value to be '
            'of Python type Foo.'
        ),
        res.description,
    )

    @dagster_type
    class Baz(object):
        pass

    res = check_dagster_type(Baz, Baz())
    assert res.success

    @dagster_type(type_check=lambda _: TypeCheck(success=True))
    class Quux(object):
        pass

    res = check_dagster_type(Quux, Quux())
    assert res.success

    @dagster_type(type_check=lambda _: TypeCheck(success=False))
    class Corge(object):
        pass

    res = check_dagster_type(Corge, Corge())
    assert not res.success

    @dagster_type(type_check=lambda _: TypeCheck(True, 'a_check', []))
    class Garble(object):
        pass

    res = check_dagster_type(Garble, Garble())
    assert isinstance(res, TypeCheck)
    assert res.success
    assert res.description == 'a_check'

    @dagster_type(type_check=lambda _: True)
    class Bboo(object):
        pass

    res = check_dagster_type(Bboo, Bboo())
    assert isinstance(res, TypeCheck)
    assert res.success

    @dagster_type(type_check=lambda _: False)
    class Bboott(object):
        pass

    res = check_dagster_type(Bboott, Bboott())
    assert isinstance(res, TypeCheck)
    assert not res.success
