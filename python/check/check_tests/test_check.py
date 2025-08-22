import pytest

import check
from check import (ParameterCheckError, ElementCheckError, CheckError, NotImplementedCheckError)


def test_int_param():
    assert check.int_param(-1, 'param_name') == -1
    assert check.int_param(0, 'param_name') == 0
    assert check.int_param(1, 'param_name') == 1

    with pytest.raises(ParameterCheckError):
        check.int_param(None, 'param_name')

    with pytest.raises(ParameterCheckError):
        check.int_param('s', 'param_name')


def test_opt_int_param():
    assert check.opt_int_param(-1, 'param_name') == -1
    assert check.opt_int_param(0, 'param_name') == 0
    assert check.opt_int_param(1, 'param_name') == 1
    assert check.opt_int_param(None, 'param_name') is None

    with pytest.raises(ParameterCheckError):
        check.opt_int_param('s', 'param_name')


def test_list_param():
    assert check.list_param([], 'list_param') == []

    with pytest.raises(ParameterCheckError):
        check.list_param(None, 'list_param')

    with pytest.raises(ParameterCheckError):
        check.list_param('3u4', 'list_param')


def test_typed_list_param():
    class Foo:
        pass

    class Bar:
        pass

    assert check.list_param([], 'list_param', Foo) == []
    foo_list = [Foo()]
    assert check.list_param(foo_list, 'list_param', Foo) == foo_list

    with pytest.raises(CheckError):
        check.list_param([Bar()], 'list_param', Foo)

    with pytest.raises(CheckError):
        check.list_param([None], 'list_param', Foo)


def test_opt_list_param():
    assert check.opt_list_param(None, 'list_param') == []
    assert check.opt_list_param([], 'list_param') == []
    obj_list = [1]
    assert check.list_param(obj_list, 'list_param') == obj_list

    with pytest.raises(ParameterCheckError):
        check.opt_list_param(0, 'list_param')

    with pytest.raises(ParameterCheckError):
        check.opt_list_param('', 'list_param')

    with pytest.raises(ParameterCheckError):
        check.opt_list_param('3u4', 'list_param')


def test_opt_typed_list_param():
    class Foo:
        pass

    class Bar:
        pass

    assert check.opt_list_param(None, 'list_param', Foo) == []
    assert check.opt_list_param([], 'list_param', Foo) == []
    foo_list = [Foo()]
    assert check.opt_list_param(foo_list, 'list_param', Foo) == foo_list

    with pytest.raises(CheckError):
        check.opt_list_param([Bar()], 'list_param', Foo)

    with pytest.raises(CheckError):
        check.opt_list_param([None], 'list_param', Foo)


def test_dict_param():
    assert check.dict_param({}, 'dict_param') == {}
    ddict = {'a': 2}
    assert check.dict_param(ddict, 'dict_param') == ddict

    with pytest.raises(ParameterCheckError):
        check.dict_param(None, 'dict_param')

    with pytest.raises(ParameterCheckError):
        check.dict_param(0, 'dict_param')

    with pytest.raises(ParameterCheckError):
        check.dict_param(1, 'dict_param')

    with pytest.raises(ParameterCheckError):
        check.dict_param('foo', 'dict_param')

    with pytest.raises(ParameterCheckError):
        check.dict_param(['foo'], 'dict_param')

    with pytest.raises(ParameterCheckError):
        check.dict_param([], 'dict_param')


def test_dict_param_with_type():
    str_to_int = {'str': 1}
    assert check.dict_param(str_to_int, 'str_to_int', key_type=str, value_type=int)
    assert check.dict_param(str_to_int, 'str_to_int', value_type=int)
    assert check.dict_param(str_to_int, 'str_to_int', key_type=str)
    assert check.dict_param(str_to_int, 'str_to_int')

    assert check.dict_param({}, 'str_to_int', key_type=str, value_type=int) == {}
    assert check.dict_param({}, 'str_to_int', value_type=int) == {}
    assert check.dict_param({}, 'str_to_int', key_type=str) == {}
    assert check.dict_param({}, 'str_to_int') == {}

    class Wrong:
        pass

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, 'str_to_int', key_type=Wrong, value_type=Wrong)

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, 'str_to_int', key_type=Wrong, value_type=int)

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, 'str_to_int', key_type=str, value_type=Wrong)

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, 'str_to_int', key_type=Wrong)

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, 'str_to_int', value_type=Wrong)


def test_opt_dict_param_with_type():
    str_to_int = {'str': 1}
    assert check.opt_dict_param(str_to_int, 'str_to_int', key_type=str, value_type=int)
    assert check.opt_dict_param(str_to_int, 'str_to_int', value_type=int)
    assert check.opt_dict_param(str_to_int, 'str_to_int', key_type=str)
    assert check.opt_dict_param(str_to_int, 'str_to_int')

    assert check.opt_dict_param({}, 'str_to_int', key_type=str, value_type=int) == {}
    assert check.opt_dict_param({}, 'str_to_int', value_type=int) == {}
    assert check.opt_dict_param({}, 'str_to_int', key_type=str) == {}
    assert check.opt_dict_param({}, 'str_to_int') == {}

    assert check.opt_dict_param(None, 'str_to_int', key_type=str, value_type=int) == {}
    assert check.opt_dict_param(None, 'str_to_int', value_type=int) == {}
    assert check.opt_dict_param(None, 'str_to_int', key_type=str) == {}
    assert check.opt_dict_param(None, 'str_to_int') == {}

    class Wrong:
        pass

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, 'str_to_int', key_type=Wrong, value_type=Wrong)

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, 'str_to_int', key_type=Wrong, value_type=int)

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, 'str_to_int', key_type=str, value_type=Wrong)

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, 'str_to_int', key_type=Wrong)

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, 'str_to_int', value_type=Wrong)


def test_opt_dict_param():
    assert check.opt_dict_param(None, 'opt_dict_param') == {}
    assert check.opt_dict_param({}, 'opt_dict_param') == {}
    ddict = {'a': 2}
    assert check.opt_dict_param(ddict, 'opt_dict_param') == ddict

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(0, 'opt_dict_param')

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(1, 'opt_dict_param')

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param('foo', 'opt_dict_param')

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(['foo'], 'opt_dict_param')

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param([], 'opt_dict_param')


def test_str_param():
    assert check.str_param('a', 'str_param') == 'a'
    assert check.str_param('', 'str_param') == ''
    assert check.str_param(u'a', 'unicode_param') == u'a'

    with pytest.raises(ParameterCheckError):
        check.str_param(None, 'str_param')

    with pytest.raises(ParameterCheckError):
        check.str_param(0, 'str_param')

    with pytest.raises(ParameterCheckError):
        check.str_param(1, 'str_param')


def test_opt_str_param():
    assert check.opt_str_param('a', 'str_param') == 'a'
    assert check.str_param('', 'str_param') == ''
    assert check.str_param(u'a', 'unicode_param') == u'a'
    assert check.opt_str_param(None, 'str_param') is None

    with pytest.raises(ParameterCheckError):
        check.opt_str_param(0, 'str_param')

    with pytest.raises(ParameterCheckError):
        check.opt_str_param(1, 'str_param')


def test_bool_param():
    assert check.bool_param(True, 'b') is True
    assert check.bool_param(False, 'b') is False

    with pytest.raises(ParameterCheckError):
        check.bool_param(None, 'b')

    with pytest.raises(ParameterCheckError):
        check.bool_param(0, 'b')

    with pytest.raises(ParameterCheckError):
        check.bool_param('val', 'b')


def test_opt_bool_param():
    assert check.opt_bool_param(True, 'b') is True
    assert check.opt_bool_param(False, 'b') is False
    assert check.opt_bool_param(None, 'b') is None

    with pytest.raises(ParameterCheckError):
        check.opt_bool_param(0, 'b')

    with pytest.raises(ParameterCheckError):
        check.opt_bool_param('val', 'b')


def test_callable_param():
    lamb = lambda: 1
    assert check.callable_param(lamb, 'lamb') == lamb

    with pytest.raises(ParameterCheckError):
        check.callable_param(None, 'lamb')

    with pytest.raises(ParameterCheckError):
        check.callable_param(2, 'lamb')


def test_opt_callable_param():
    lamb = lambda: 1
    assert check.opt_callable_param(lamb, 'lamb') == lamb
    assert check.opt_callable_param(None, 'lamb') is None

    with pytest.raises(ParameterCheckError):
        check.opt_callable_param(2, 'lamb')


def test_param_invariant():
    check.param_invariant(True, 'some_param')
    num_to_check = 1
    check.param_invariant(num_to_check == 1, 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant(num_to_check == 2, 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant(False, 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant(0, 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant(1, 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant('', 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant('1kjkjsf', 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant({}, 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant({234: '1kjkjsf'}, 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant([], 'some_param')

    with pytest.raises(ParameterCheckError):
        check.param_invariant([234], 'some_param')


def test_string_elem():
    ddict = {'a_str': 'a', 'a_num': 1, 'a_none': None}

    assert check.str_elem(ddict, 'a_str') == 'a'

    with pytest.raises(ElementCheckError):
        assert check.str_elem(ddict, 'a_none')

    with pytest.raises(ElementCheckError):
        check.str_elem(ddict, 'a_num')


def test_bool_elem():
    ddict = {'a_true': True, 'a_str': 'a', 'a_num': 1, 'a_none': None}

    assert check.bool_elem(ddict, 'a_true') is True

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, 'a_none')

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, 'a_num')

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, 'a_str')


def test_invariant():
    assert check.invariant(True)

    with pytest.raises(CheckError):
        check.invariant(False)

    with pytest.raises(CheckError, match='Some Unique String'):
        check.invariant(False, 'Some Unique String')

    empty_list = []

    with pytest.raises(CheckError, match='Invariant condition must be boolean'):
        check.invariant(empty_list)


def test_failed():
    with pytest.raises(CheckError, match='some desc'):
        check.failed('some desc')

    with pytest.raises(CheckError, match='must be a string'):
        check.failed(0)


def test_not_implemented():
    with pytest.raises(NotImplementedCheckError, match='some string'):
        check.not_implemented('some string')


def test_inst():
    class Foo:
        pass

    class Bar:
        pass

    obj = Foo()

    assert check.inst(obj, Foo) == obj

    with pytest.raises(CheckError, match='not a Bar'):
        check.inst(Foo(), Bar)


def test_param_inst():
    class Foo:
        pass

    class Bar:
        pass

    obj = Foo()

    assert check.inst_param(obj, 'obj', Foo) == obj

    with pytest.raises(ParameterCheckError, match='not a Bar'):
        check.inst_param(None, 'obj', Bar)

    with pytest.raises(ParameterCheckError, match='not a Bar'):
        check.inst_param(Foo(), 'obj', Bar)


def test_opt_param_inst():
    class Foo:
        pass

    class Bar:
        pass

    obj = Foo()

    assert check.opt_inst_param(obj, 'obj', Foo) == obj
    assert check.opt_inst_param(None, 'obj', Foo) is None
    assert check.opt_inst_param(None, 'obj', Bar) is None

    with pytest.raises(ParameterCheckError, match='not a Bar'):
        check.opt_inst_param(Foo(), 'obj', Bar)


def test_dict_elem():
    dict_value = {'blah': 'blahblah'}
    ddict = {'dictkey': dict_value, 'stringkey': 'A', 'nonekey': None}

    assert check.dict_elem(ddict, 'dictkey') == dict_value

    with pytest.raises(CheckError):
        check.dict_elem(ddict, 'stringkey')

    with pytest.raises(CheckError):
        check.dict_elem(ddict, 'nonekey')

    with pytest.raises(CheckError):
        check.dict_elem(ddict, 'nonexistantkey')


def test_opt_dict_elem():
    dict_value = {'blah': 'blahblah'}
    ddict = {'dictkey': dict_value, 'stringkey': 'A', 'nonekey': None}

    assert check.opt_dict_elem(ddict, 'dictkey') == dict_value
    assert check.opt_dict_elem(ddict, 'nonekey') is None
    assert check.opt_dict_elem(ddict, 'nonexistantkey') is None

    with pytest.raises(CheckError):
        check.opt_dict_elem(ddict, 'stringkey')
