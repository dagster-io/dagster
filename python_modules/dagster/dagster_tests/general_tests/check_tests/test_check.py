import re
import sys
from collections import defaultdict
from contextlib import contextmanager

import pytest
from dagster import check
from dagster.check import (
    CheckError,
    ElementCheckError,
    NotImplementedCheckError,
    ParameterCheckError,
)
from dagster.utils import frozendict, frozenlist


def test_int_param():
    assert check.int_param(-1, "param_name") == -1
    assert check.int_param(0, "param_name") == 0
    assert check.int_param(1, "param_name") == 1

    with pytest.raises(ParameterCheckError):
        check.int_param(None, "param_name")

    with pytest.raises(ParameterCheckError):
        check.int_param("s", "param_name")


def test_int_value_param():
    assert check.int_value_param(-1, -1, "param_name") == -1
    with pytest.raises(ParameterCheckError):
        check.int_value_param(None, -1, "param_name")

    with pytest.raises(ParameterCheckError):
        check.int_value_param(1, 0, "param_name")


def test_opt_int_param():
    assert check.opt_int_param(-1, "param_name") == -1
    assert check.opt_int_param(0, "param_name") == 0
    assert check.opt_int_param(1, "param_name") == 1
    assert check.opt_int_param(None, "param_name") is None

    with pytest.raises(ParameterCheckError):
        check.opt_int_param("s", "param_name")


def test_float_param():
    assert check.float_param(-1.0, "param_name") == -1.0
    assert check.float_param(0.0, "param_name") == 0.0
    assert check.float_param(1.1, "param_name") == 1.1

    with pytest.raises(ParameterCheckError):
        check.float_param(None, "param_name")

    with pytest.raises(ParameterCheckError):
        check.float_param("s", "param_name")

    with pytest.raises(ParameterCheckError):
        check.float_param(1, "param_name")

    with pytest.raises(ParameterCheckError):
        check.float_param(0, "param_name")


def test_opt_float_param():
    assert check.opt_float_param(-1.0, "param_name") == -1.0
    assert check.opt_float_param(0.0, "param_name") == 0.0
    assert check.opt_float_param(1.1, "param_name") == 1.1
    assert check.opt_float_param(None, "param_name") is None

    with pytest.raises(ParameterCheckError):
        check.opt_float_param("s", "param_name")


def test_list_param():
    assert check.list_param([], "list_param") == []
    assert check.list_param(frozenlist(), "list_param") == []

    assert check.list_param(["foo"], "list_param", of_type=str) == ["foo"]

    with pytest.raises(ParameterCheckError):
        check.list_param(None, "list_param")

    with pytest.raises(ParameterCheckError):
        check.list_param("3u4", "list_param")

    with pytest.raises(CheckError):
        check.list_param(["foo"], "list_param", of_type=int)


def test_set_param():
    assert check.set_param(set(), "set_param") == set()
    assert check.set_param(frozenset(), "set_param") == set()

    with pytest.raises(ParameterCheckError):
        check.set_param(None, "set_param")

    with pytest.raises(ParameterCheckError):
        check.set_param("3u4", "set_param")

    obj_set = {1}
    assert check.set_param(obj_set, "set_param") == obj_set

    obj_set_two = {1, 1, 2}
    obj_set_two_deduped = {1, 2}
    assert check.set_param(obj_set_two, "set_param") == obj_set_two_deduped
    assert check.set_param(obj_set_two, "set_param", of_type=int) == obj_set_two_deduped

    with pytest.raises(CheckError, match="Did you pass a class"):
        check.set_param({str}, "set_param", of_type=int)

    with pytest.raises(CheckError, match="Member of set mismatches type"):
        check.set_param({"foo"}, "set_param", of_type=int)


def test_typed_list_param():
    class Foo:
        pass

    class Bar:
        pass

    assert check.list_param([], "list_param", Foo) == []
    foo_list = [Foo()]
    assert check.list_param(foo_list, "list_param", Foo) == foo_list

    with pytest.raises(CheckError):
        check.list_param([Bar()], "list_param", Foo)

    with pytest.raises(CheckError):
        check.list_param([None], "list_param", Foo)


def test_is_tuple():
    assert check.is_tuple(()) == ()

    with pytest.raises(CheckError):
        check.is_tuple(None)

    with pytest.raises(CheckError):
        check.is_tuple("3u4")

    with pytest.raises(CheckError, match="Did you pass a class"):
        check.is_tuple((str,), of_type=int)


def test_typed_is_tuple():
    class Foo:
        pass

    class Bar:
        pass

    assert check.is_tuple((), Foo) == ()
    foo_tuple = (Foo(),)
    assert check.is_tuple(foo_tuple, Foo) == foo_tuple

    with pytest.raises(CheckError):
        check.is_tuple((Bar(),), Foo)

    with pytest.raises(CheckError):
        check.is_tuple((None,), Foo)


def test_typed_is_list():
    class Foo:
        pass

    class Bar:
        pass

    assert check.is_list([], Foo) == []
    foo_list = [Foo()]
    assert check.is_list(foo_list, of_type=Foo) == foo_list

    assert check.is_list([Foo(), Bar()], of_type=(Foo, Bar))

    with pytest.raises(CheckError):
        check.is_list([Bar()], of_type=Foo)

    with pytest.raises(CheckError):
        check.is_list([None], of_type=Foo)

    with pytest.raises(CheckError):
        check.is_list([Foo(), Bar(), ""], of_type=(Foo, Bar))


def test_opt_list_param():
    assert check.opt_list_param(None, "list_param") == []
    assert check.opt_list_param(None, "list_param", of_type=str) == []
    assert check.opt_list_param([], "list_param") == []
    assert check.opt_list_param(frozenlist(), "list_param") == []
    obj_list = [1]
    assert check.list_param(obj_list, "list_param") == obj_list
    assert check.opt_list_param(["foo"], "list_param", of_type=str) == ["foo"]

    with pytest.raises(ParameterCheckError):
        check.opt_list_param(0, "list_param")

    with pytest.raises(ParameterCheckError):
        check.opt_list_param("", "list_param")

    with pytest.raises(ParameterCheckError):
        check.opt_list_param("3u4", "list_param")

    with pytest.raises(CheckError):
        check.opt_list_param(["foo"], "list_param", of_type=int)


def test_opt_set_param():
    assert check.opt_set_param(None, "set_param") == set()
    assert check.opt_set_param(set(), "set_param") == set()
    assert check.opt_set_param(frozenset(), "set_param") == set()
    assert check.opt_set_param({3}, "set_param") == {3}

    with pytest.raises(ParameterCheckError):
        check.opt_set_param(0, "set_param")

    with pytest.raises(ParameterCheckError):
        check.opt_set_param("", "set_param")

    with pytest.raises(ParameterCheckError):
        check.opt_set_param("3u4", "set_param")


def test_opt_nullable_list_param():
    assert check.opt_nullable_list_param(None, "list_param") is None
    assert check.opt_nullable_list_param([], "list_param") == []
    assert check.opt_nullable_list_param(frozenlist(), "list_param") == []
    obj_list = [1]
    assert check.opt_nullable_list_param(obj_list, "list_param") == obj_list

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_list_param(0, "list_param")

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_list_param("", "list_param")

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_list_param("3u4", "list_param")


def test_opt_typed_list_param():
    class Foo:
        pass

    class Bar:
        pass

    assert check.opt_list_param(None, "list_param", Foo) == []
    assert check.opt_list_param([], "list_param", Foo) == []
    foo_list = [Foo()]
    assert check.opt_list_param(foo_list, "list_param", Foo) == foo_list

    with pytest.raises(CheckError):
        check.opt_list_param([Bar()], "list_param", Foo)

    with pytest.raises(CheckError):
        check.opt_list_param([None], "list_param", Foo)


def test_dict_param():
    assert check.dict_param({}, "dict_param") == {}
    assert check.dict_param(frozendict(), "dict_param") == {}
    ddict = {"a": 2}
    assert check.dict_param(ddict, "dict_param") == ddict

    with pytest.raises(ParameterCheckError):
        check.dict_param(None, "dict_param")

    with pytest.raises(ParameterCheckError):
        check.dict_param(0, "dict_param")

    with pytest.raises(ParameterCheckError):
        check.dict_param(1, "dict_param")

    with pytest.raises(ParameterCheckError):
        check.dict_param("foo", "dict_param")

    with pytest.raises(ParameterCheckError):
        check.dict_param(["foo"], "dict_param")

    with pytest.raises(ParameterCheckError):
        check.dict_param([], "dict_param")


def test_dict_param_with_type():
    str_to_int = {"str": 1}
    assert check.dict_param(str_to_int, "str_to_int", key_type=str, value_type=int)
    assert check.dict_param(str_to_int, "str_to_int", value_type=int)
    assert check.dict_param(str_to_int, "str_to_int", key_type=str)
    assert check.dict_param(str_to_int, "str_to_int")

    assert check.dict_param({}, "str_to_int", key_type=str, value_type=int) == {}
    assert check.dict_param({}, "str_to_int", value_type=int) == {}
    assert check.dict_param({}, "str_to_int", key_type=str) == {}
    assert check.dict_param({}, "str_to_int") == {}

    assert check.dict_param(
        {"str": 1, "str2": "str", 1: "str", 2: "str"},
        "multi_type_dict",
        key_type=(str, int),
        value_type=(str, int),
    )

    class Wrong:
        pass

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, "str_to_int", key_type=Wrong, value_type=Wrong)

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, "str_to_int", key_type=Wrong, value_type=int)

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, "str_to_int", key_type=str, value_type=Wrong)

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, "str_to_int", key_type=Wrong)

    class AlsoWrong:
        pass

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, "str_to_int", key_type=(Wrong, AlsoWrong))

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, "str_to_int", value_type=(Wrong, AlsoWrong))


def test_opt_dict_param_with_type():
    str_to_int = {"str": 1}
    assert check.opt_dict_param(str_to_int, "str_to_int", key_type=str, value_type=int)
    assert check.opt_dict_param(str_to_int, "str_to_int", value_type=int)
    assert check.opt_dict_param(str_to_int, "str_to_int", key_type=str)
    assert check.opt_dict_param(str_to_int, "str_to_int")

    assert check.opt_dict_param({}, "str_to_int", key_type=str, value_type=int) == {}
    assert check.opt_dict_param({}, "str_to_int", value_type=int) == {}
    assert check.opt_dict_param({}, "str_to_int", key_type=str) == {}
    assert check.opt_dict_param({}, "str_to_int") == {}

    assert check.opt_dict_param(None, "str_to_int", key_type=str, value_type=int) == {}
    assert check.opt_dict_param(None, "str_to_int", value_type=int) == {}
    assert check.opt_dict_param(None, "str_to_int", key_type=str) == {}
    assert check.opt_dict_param(None, "str_to_int") == {}

    assert check.opt_dict_param(
        {"str": 1, "str2": "str", 1: "str", 2: "str"},
        "multi_type_dict",
        key_type=(str, int),
        value_type=(str, int),
    )

    class Wrong:
        pass

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, "str_to_int", key_type=Wrong, value_type=Wrong)

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, "str_to_int", key_type=Wrong, value_type=int)

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, "str_to_int", key_type=str, value_type=Wrong)

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, "str_to_int", key_type=Wrong)

    with pytest.raises(CheckError):
        assert check.opt_dict_param(str_to_int, "str_to_int", value_type=Wrong)

    class AlsoWrong:
        pass

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, "str_to_int", key_type=(Wrong, AlsoWrong))

    with pytest.raises(CheckError):
        assert check.dict_param(str_to_int, "str_to_int", value_type=(Wrong, AlsoWrong))


def test_opt_dict_param():
    assert check.opt_dict_param(None, "opt_dict_param") == {}
    assert check.opt_dict_param({}, "opt_dict_param") == {}
    assert check.opt_dict_param(frozendict(), "opt_dict_param") == {}
    ddict = {"a": 2}
    assert check.opt_dict_param(ddict, "opt_dict_param") == ddict

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(0, "opt_dict_param")

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(1, "opt_dict_param")

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param("foo", "opt_dict_param")

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(["foo"], "opt_dict_param")

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param([], "opt_dict_param")


def test_opt_nullable_dict_param():
    assert check.opt_nullable_dict_param(None, "opt_nullable_dict_param") is None
    assert check.opt_nullable_dict_param({}, "opt_nullable_dict_param") == {}
    assert check.opt_nullable_dict_param(frozendict(), "opt_nullable_dict_param") == {}
    ddict = {"a": 2}
    assert check.opt_nullable_dict_param(ddict, "opt_nullable_dict_param") == ddict

    class Foo:
        pass

    class Bar(Foo):
        pass

    ddict_class = {"a": Bar}
    assert (
        check.opt_nullable_dict_param(ddict_class, "opt_nullable_dict_param", value_class=Foo)
        == ddict_class
    )

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_dict_param(1, "opt_nullable_dict_param")

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_dict_param("foo", "opt_nullable_dict_param")


def test_str_param():
    assert check.str_param("a", "str_param") == "a"
    assert check.str_param("", "str_param") == ""
    assert check.str_param("a", "unicode_param") == "a"

    with pytest.raises(ParameterCheckError):
        check.str_param(None, "str_param")

    with pytest.raises(ParameterCheckError):
        check.str_param(0, "str_param")

    with pytest.raises(ParameterCheckError):
        check.str_param(1, "str_param")


def test_opt_str_param():
    assert check.opt_str_param("a", "str_param") == "a"
    assert check.opt_str_param("", "str_param") == ""
    assert check.opt_str_param("a", "unicode_param") == "a"
    assert check.opt_str_param(None, "str_param") is None
    assert check.opt_str_param(None, "str_param", "foo") == "foo"

    with pytest.raises(ParameterCheckError):
        check.opt_str_param(0, "str_param")

    with pytest.raises(ParameterCheckError):
        check.opt_str_param(1, "str_param")


def test_opt_nonempty_str_param():
    assert check.opt_nonempty_str_param("a", "str_param") == "a"
    assert check.opt_nonempty_str_param("", "str_param") is None
    assert check.opt_nonempty_str_param("", "str_param", "foo") == "foo"
    assert check.opt_nonempty_str_param("a", "unicode_param") == "a"
    assert check.opt_nonempty_str_param(None, "str_param") is None
    assert check.opt_nonempty_str_param(None, "str_param", "foo") == "foo"

    with pytest.raises(ParameterCheckError):
        check.opt_nonempty_str_param(0, "str_param")

    with pytest.raises(ParameterCheckError):
        check.opt_nonempty_str_param(1, "str_param")


def test_bool_param():
    assert check.bool_param(True, "b") is True
    assert check.bool_param(False, "b") is False

    with pytest.raises(ParameterCheckError):
        check.bool_param(None, "b")

    with pytest.raises(ParameterCheckError):
        check.bool_param(0, "b")

    with pytest.raises(ParameterCheckError):
        check.bool_param("val", "b")


def test_opt_bool_param():
    assert check.opt_bool_param(True, "b") is True
    assert check.opt_bool_param(False, "b") is False
    assert check.opt_bool_param(None, "b") is None
    assert check.opt_bool_param(None, "b", True) is True
    assert check.opt_bool_param(None, "b", False) is False

    with pytest.raises(ParameterCheckError):
        check.opt_bool_param(0, "b")

    with pytest.raises(ParameterCheckError):
        check.opt_bool_param("val", "b")


def test_callable_param():
    lamb = lambda: 1
    assert check.callable_param(lamb, "lamb") == lamb

    with pytest.raises(ParameterCheckError):
        check.callable_param(None, "lamb")

    with pytest.raises(ParameterCheckError):
        check.callable_param(2, "lamb")


def test_opt_callable_param():
    lamb = lambda: 1
    assert check.opt_callable_param(lamb, "lamb") == lamb
    assert check.opt_callable_param(None, "lamb") is None
    assert check.opt_callable_param(None, "lamb", default=None) is None
    assert check.opt_callable_param(None, "lamb", default=lamb) == lamb

    with pytest.raises(ParameterCheckError):
        check.opt_callable_param(2, "lamb")


def test_param_invariant():
    check.param_invariant(True, "some_param")
    num_to_check = 1
    check.param_invariant(num_to_check == 1, "some_param")

    with pytest.raises(ParameterCheckError):
        check.param_invariant(num_to_check == 2, "some_param")

    with pytest.raises(ParameterCheckError):
        check.param_invariant(False, "some_param")

    with pytest.raises(ParameterCheckError):
        check.param_invariant(0, "some_param")

    check.param_invariant(1, "some_param")

    with pytest.raises(ParameterCheckError):
        check.param_invariant("", "some_param")

    check.param_invariant("1kjkjsf", "some_param")

    with pytest.raises(ParameterCheckError):
        check.param_invariant({}, "some_param")

    check.param_invariant({234: "1kjkjsf"}, "some_param")

    with pytest.raises(ParameterCheckError):
        check.param_invariant([], "some_param")

    check.param_invariant([234], "some_param")


def test_string_elem():
    ddict = {"a_str": "a", "a_num": 1, "a_none": None}

    assert check.str_elem(ddict, "a_str") == "a"

    with pytest.raises(ElementCheckError):
        assert check.str_elem(ddict, "a_none")

    with pytest.raises(ElementCheckError):
        check.str_elem(ddict, "a_num")


def test_opt_string_elem():
    ddict = {"a_str": "a", "a_num": 1, "a_none": None}

    assert check.opt_str_elem(ddict, "a_str") == "a"

    assert check.opt_str_elem(ddict, "a_none") == None

    assert check.opt_str_elem(ddict, "nonexistentkey") == None

    with pytest.raises(ElementCheckError):
        check.opt_str_elem(ddict, "a_num")


def test_bool_elem():
    ddict = {"a_true": True, "a_str": "a", "a_num": 1, "a_none": None}

    assert check.bool_elem(ddict, "a_true") is True

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, "a_none")

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, "a_num")

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, "a_str")


def test_float_elem():
    ddict = {"a_bool": True, "a_float": 1.0, "a_int": 1, "a_none": None, "a_str": "a"}

    assert check.float_elem(ddict, "a_float") == 1.0

    with pytest.raises(ElementCheckError):
        check.float_elem(ddict, "a_bool")

    with pytest.raises(ElementCheckError):
        check.float_elem(ddict, "a_int")

    with pytest.raises(ElementCheckError):
        check.float_elem(ddict, "a_none")

    with pytest.raises(ElementCheckError):
        check.float_elem(ddict, "a_str")


def test_opt_float_elem():
    ddict = {"a_bool": True, "a_float": 1.0, "a_int": 1, "a_none": None, "a_str": "a"}

    assert check.opt_float_elem(ddict, "a_float") == 1.0

    assert check.opt_float_elem(ddict, "a_none") == None

    assert check.opt_float_elem(ddict, "nonexistentkey") == None

    with pytest.raises(ElementCheckError):
        check.opt_float_elem(ddict, "a_bool")

    with pytest.raises(ElementCheckError):
        check.opt_float_elem(ddict, "a_int")

    with pytest.raises(ElementCheckError):
        check.opt_float_elem(ddict, "a_str")


def test_int_elem():
    ddict = {"a_bool": True, "a_float": 1.0, "a_int": 1, "a_none": None, "a_str": "a"}

    assert check.int_elem(ddict, "a_int") == 1

    assert check.int_elem(ddict, "a_bool") == True

    with pytest.raises(ElementCheckError):
        check.int_elem(ddict, "a_float")

    with pytest.raises(ElementCheckError):
        check.int_elem(ddict, "a_none")

    with pytest.raises(ElementCheckError):
        check.int_elem(ddict, "a_str")


def test_opt_int_elem():
    ddict = {"a_bool": True, "a_float": 1.0, "a_int": 1, "a_none": None, "a_str": "a"}

    assert check.opt_int_elem(ddict, "a_int") == 1

    assert check.opt_int_elem(ddict, "a_none") == None

    assert check.opt_int_elem(ddict, "nonexistentkey") == None

    assert check.opt_int_elem(ddict, "a_bool") == True

    with pytest.raises(ElementCheckError):
        check.opt_int_elem(ddict, "a_float")

    with pytest.raises(ElementCheckError):
        check.opt_int_elem(ddict, "a_str")


def test_invariant():
    assert check.invariant(True)

    with pytest.raises(CheckError):
        check.invariant(False)

    with pytest.raises(CheckError, match="Some Unique String"):
        check.invariant(False, "Some Unique String")

    empty_list = []

    with pytest.raises(CheckError, match="Invariant failed"):
        check.invariant(empty_list)


def test_failed():
    with pytest.raises(CheckError, match="some desc"):
        check.failed("some desc")

    with pytest.raises(CheckError, match="must be a string"):
        check.failed(0)


def test_not_implemented():
    with pytest.raises(NotImplementedCheckError, match="some string"):
        check.not_implemented("some string")

    with pytest.raises(CheckError, match="desc argument must be a string"):
        check.not_implemented(None)


def test_inst():
    class Foo:
        pass

    class Bar:
        pass

    obj = Foo()

    assert check.inst(obj, Foo) == obj

    with pytest.raises(CheckError, match="not a Bar"):
        check.inst(Foo(), Bar)

    with pytest.raises(CheckError, match="Desc: Expected only a Bar"):
        check.inst(Foo(), Bar, "Expected only a Bar")

    with pytest.raises(CheckError, match=re.escape("not one of ['Bar', 'Foo']")):
        check.inst(1, (Foo, Bar))

    with pytest.raises(CheckError, match=re.escape("not one of ['Bar', 'Foo']")):
        check.inst(1, (Foo, Bar), desc="a desc")

    with pytest.raises(CheckError, match=re.escape("Desc: a desc")):
        check.inst(1, (Foo, Bar), desc="a desc")


def test_inst_param():
    class Foo:
        pass

    class Bar:
        pass

    class Baaz:
        pass

    obj = Foo()

    assert check.inst_param(obj, "obj", Foo) == obj

    with pytest.raises(ParameterCheckError, match="not a Bar"):
        check.inst_param(None, "obj", Bar)

    with pytest.raises(ParameterCheckError, match="not a Bar"):
        check.inst_param(Bar, "obj", Bar)

    with pytest.raises(ParameterCheckError, match="not a Bar"):
        check.inst_param(Foo(), "obj", Bar)

    with pytest.raises(ParameterCheckError, match=r"not one of \['Bar', 'Foo'\]"):
        check.inst_param(None, "obj", (Foo, Bar))

    with pytest.raises(ParameterCheckError, match=r"not one of \['Bar', 'Foo'\]"):
        check.inst_param(Baaz(), "obj", (Foo, Bar))


def test_opt_inst_param():
    class Foo:
        pass

    class Bar:
        pass

    class Baaz:
        pass

    obj = Foo()

    assert check.opt_inst_param(obj, "obj", Foo) == obj
    assert check.opt_inst_param(None, "obj", Foo) is None
    assert check.opt_inst_param(None, "obj", Bar) is None

    with pytest.raises(ParameterCheckError, match="not a Bar"):
        check.opt_inst_param(Bar, "obj", Bar)

    with pytest.raises(ParameterCheckError, match="not a Bar"):
        check.opt_inst_param(Foo(), "obj", Bar)

    # check defaults

    default_obj = Foo()

    assert check.opt_inst_param(None, "obj", Foo, default_obj) is default_obj

    assert check.opt_inst_param(None, "obj", (Foo, Bar)) is None

    with pytest.raises(ParameterCheckError, match=r"not one of \['Bar', 'Foo'\]"):
        check.inst_param(Baaz(), "obj", (Foo, Bar))


def test_dict_elem():
    dict_value = {"blah": "blahblah"}
    ddict = {"dictkey": dict_value, "stringkey": "A", "nonekey": None}

    assert check.dict_elem(ddict, "dictkey") == dict_value

    with pytest.raises(CheckError):
        check.dict_elem(ddict, "stringkey")

    with pytest.raises(CheckError):
        check.dict_elem(ddict, "nonekey")

    with pytest.raises(CheckError):
        check.dict_elem(ddict, "nonexistantkey")


def test_opt_dict_elem():
    dict_value = {"blah": "blahblah"}
    ddict = {"dictkey": dict_value, "stringkey": "A", "nonekey": None}

    assert check.opt_dict_elem(ddict, "dictkey") == dict_value
    assert check.opt_dict_elem(ddict, "nonekey") == {}
    assert check.opt_dict_elem(ddict, "nonexistantkey") == {}

    with pytest.raises(CheckError):
        check.opt_dict_elem(ddict, "stringkey")


def test_list_elem():
    list_value = ["blah", "blahblah"]
    ddict = {"listkey": list_value, "stringkey": "A", "nonekey": None}

    assert check.list_elem(ddict, "listkey") == list_value
    assert check.list_elem(ddict, "listkey", of_type=str) == list_value

    with pytest.raises(CheckError):
        assert check.list_elem(ddict, "nonekey") == []

    with pytest.raises(CheckError):
        assert check.list_elem(ddict, "nonexistantkey") == []

    with pytest.raises(CheckError):
        check.list_elem(ddict, "stringkey")

    with pytest.raises(CheckError):
        check.list_elem(ddict, "listkey", of_type=int)


def test_opt_list_elem():
    list_value = ["blah", "blahblah"]
    ddict = {"listkey": list_value, "stringkey": "A", "nonekey": None}

    assert check.opt_list_elem(ddict, "listkey") == list_value
    assert check.opt_list_elem(ddict, "listkey", of_type=str) == list_value
    assert check.opt_list_elem(ddict, "nonekey") == []
    assert check.opt_list_elem(ddict, "nonexistantkey") == []

    with pytest.raises(CheckError):
        check.opt_list_elem(ddict, "stringkey")

    with pytest.raises(CheckError):
        check.opt_list_elem(ddict, "listkey", of_type=int)


def test_not_none_param():
    assert check.not_none_param(1, "fine")
    check.not_none_param(0, "zero is fine")
    check.not_none_param("", "empty str is fine")

    with pytest.raises(CheckError):
        check.not_none_param(None, "none fails")


def test_is_callable():
    def fn():
        pass

    assert check.is_callable(fn) == fn
    assert check.is_callable(lambda: None)
    assert check.is_callable(lambda: None, "some desc")

    with pytest.raises(CheckError):
        check.is_callable(None)

    with pytest.raises(CheckError):
        check.is_callable(1)

    with pytest.raises(CheckError, match="some other desc"):
        check.is_callable(1, "some other desc")


def test_tuple_param():
    assert check.tuple_param((1, 2), "something")

    with pytest.raises(CheckError):
        assert check.tuple_param(None, "something")

    with pytest.raises(CheckError):
        assert check.tuple_param(1, "something")

    with pytest.raises(CheckError):
        assert check.tuple_param([1], "something")

    with pytest.raises(CheckError):
        assert check.tuple_param({1: 2}, "something")

    with pytest.raises(CheckError):
        assert check.tuple_param("kdjfkd", "something")

    assert check.tuple_param((3, 4), "something", of_type=int)
    assert check.tuple_param(("foo", "bar"), "something", of_type=str)

    assert check.tuple_param((3, 4), "something", of_type=(int, int))
    assert check.tuple_param((3, 4), "something", of_type=(int, int))
    assert check.tuple_param((3, "bar"), "something", of_type=(int, str))

    with pytest.raises(CheckError):
        check.tuple_param((3, 4, 5), "something", of_type=(int, int))

    with pytest.raises(CheckError):
        check.tuple_param((3, 4), "something", of_type=(int, int, int))

    with pytest.raises(CheckError):
        check.tuple_param((3, 4), "something", of_type=(int, str))

    with pytest.raises(CheckError):
        check.tuple_param((3, 4), "something", of_type=(str, str))


@pytest.mark.xfail(reason="https://github.com/dagster-io/dagster/issues/3299")
def test_non_variadic_union_type_is_tuple():
    class Foo:
        pass

    class Bar:
        pass

    # this is the behavior of isinstance
    foo_tuple = (Foo(),)
    for item in foo_tuple:
        assert isinstance(item, (Foo, Bar))

    # This call fails:
    # This does not call isinstance on tuple member and instead does
    # non-variadic typing. It is impossible to check that each
    # member is Foo or Bar given current API design
    check.is_tuple(foo_tuple, of_type=(Foo, Bar))


def test_matrix_param():
    assert check.matrix_param([[1, 2], [2, 3]], "something")

    with pytest.raises(CheckError):
        assert check.matrix_param(None, "something")

    with pytest.raises(CheckError):
        assert check.matrix_param([1, 2, 4], "something")

    with pytest.raises(CheckError):
        assert check.matrix_param([], "something")

    with pytest.raises(CheckError):
        assert check.matrix_param([[1, 2], 3], "soemthing")

    with pytest.raises(CheckError):
        assert check.matrix_param([[1, 2], [3.0, 4.1]], "something", of_type=int)

    with pytest.raises(CheckError):
        assert check.matrix_param([[1, 2], [2, 3, 4]], "something")


def test_opt_tuple_param():
    assert check.opt_tuple_param((1, 2), "something")
    assert check.opt_tuple_param(None, "something") is None
    assert check.opt_tuple_param(None, "something", (2)) == (2)

    with pytest.raises(CheckError):
        check.opt_tuple_param(1, "something")

    with pytest.raises(CheckError):
        check.opt_tuple_param([1], "something")

    with pytest.raises(CheckError):
        check.opt_tuple_param({1: 2}, "something")

    with pytest.raises(CheckError):
        check.opt_tuple_param("kdjfkd", "something")

    assert check.opt_tuple_param((3, 4), "something", of_type=int)
    assert check.opt_tuple_param(("foo", "bar"), "something", of_type=str)

    assert check.opt_tuple_param((3, 4), "something", of_type=(int, int))
    assert check.opt_tuple_param((3, 4), "something", of_type=(int, int))
    assert check.opt_tuple_param((3, "bar"), "something", of_type=(int, str))

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, 4, 5), "something", of_type=(int, int))

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, 4), "something", of_type=(int, int, int))

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, 4), "something", of_type=(int, str))

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, 4), "something", of_type=(str, str))


def test_opt_type_param():
    class Foo:
        pass

    assert check.opt_type_param(int, "foo")
    assert check.opt_type_param(Foo, "foo")

    assert check.opt_type_param(None, "foo") is None
    assert check.opt_type_param(None, "foo", Foo) is Foo

    with pytest.raises(CheckError):
        check.opt_type_param(check, "foo")

    with pytest.raises(CheckError):
        check.opt_type_param(234, "foo")

    with pytest.raises(CheckError):
        check.opt_type_param("bar", "foo")

    with pytest.raises(CheckError):
        check.opt_type_param(Foo(), "foo")


def test_type_param():
    class Bar:
        pass

    assert check.type_param(int, "foo")
    assert check.type_param(Bar, "foo")

    with pytest.raises(CheckError):
        check.type_param(None, "foo")

    with pytest.raises(CheckError):
        check.type_param(check, "foo")

    with pytest.raises(CheckError):
        check.type_param(234, "foo")

    with pytest.raises(CheckError):
        check.type_param("bar", "foo")

    with pytest.raises(CheckError):
        check.type_param(Bar(), "foo")


def test_subclass_param():
    class Super:
        pass

    class Sub(Super):
        pass

    class Alone:
        pass

    assert check.subclass_param(Sub, "foo", Super)

    with pytest.raises(CheckError):
        assert check.subclass_param(Alone, "foo", Super)

    with pytest.raises(CheckError):
        assert check.subclass_param("value", "foo", Super)

    assert check.opt_subclass_param(Sub, "foo", Super)
    assert check.opt_subclass_param(None, "foo", Super) is None

    with pytest.raises(CheckError):
        assert check.opt_subclass_param(Alone, "foo", Super)

    with pytest.raises(CheckError):
        assert check.opt_subclass_param("value", "foo", Super)


@contextmanager
def raises_with_message(exc_type, message_text):
    with pytest.raises(exc_type) as exc_info:
        yield

    assert str(exc_info.value) == message_text


def is_python_three():
    return sys.version_info[0] >= 3


def test_two_dim_dict():
    assert check.two_dim_dict_param({}, "foo") == {}
    assert check.two_dim_dict_param({"key": {}}, "foo")
    assert check.two_dim_dict_param({"key": {"key2": 2}}, "foo")

    # make sure default dict passes
    default_dict = defaultdict(dict)
    default_dict["key"]["key2"] = 2
    assert check.two_dim_dict_param(default_dict, "foo")

    with raises_with_message(
        CheckError,
        """Param "foo" is not a dict. Got None which is type <class 'NoneType'>."""
        if is_python_three()
        else """Param "foo" is not a dict. Got None which is type <type 'NoneType'>.""",
    ):
        check.two_dim_dict_param(None, "foo")

    with raises_with_message(
        CheckError,
        "Value in dictionary mismatches expected type for key int_value. Expected value "
        "of type <class 'dict'>. Got value 2 of type <class 'int'>."
        if is_python_three()
        else "Value in dictionary mismatches expected type for key int_value. Expected value "
        "of type <type 'dict'>. Got value 2 of type <type 'int'>.",
    ):
        check.two_dim_dict_param({"int_value": 2}, "foo")

    with raises_with_message(
        CheckError,
        "Value in dictionary mismatches expected type for key level_two_value_mismatch. "
        "Expected value of type <class 'str'>. Got value 2 of type <class 'int'>."
        if is_python_three()
        else "Value in dictionary mismatches expected type for key level_two_value_mismatch. "
        "Expected value of type (<type 'basestring'>,). Got value 2 of type <type 'int'>.",
    ):
        check.two_dim_dict_param(
            {"level_one_key": {"level_two_value_mismatch": 2}}, "foo", value_type=str
        )

    with raises_with_message(
        CheckError,
        "Key in dictionary mismatches type. Expected <class 'int'>. Got 'key'"
        if is_python_three()
        else "Key in dictionary mismatches type. Expected <type 'int'>. Got 'key'",
    ):
        assert check.two_dim_dict_param({"key": {}}, "foo", key_type=int)

    with raises_with_message(
        CheckError,
        "Key in dictionary mismatches type. Expected <class 'int'>. Got 'level_two_key'"
        if is_python_three()
        else "Key in dictionary mismatches type. Expected <type 'int'>. Got 'level_two_key'",
    ):
        assert check.two_dim_dict_param({1: {"level_two_key": "something"}}, "foo", key_type=int)


def test_opt_two_dim_dict_parm():
    assert check.opt_two_dim_dict_param({}, "foo") == {}
    assert check.opt_two_dim_dict_param({"key": {}}, "foo")
    assert check.opt_two_dim_dict_param({"key": {"key2": 2}}, "foo")
    assert check.opt_two_dim_dict_param(None, "foo") == {}

    with pytest.raises(CheckError):
        assert check.opt_two_dim_dict_param("str", "foo")


def test_generator_param():
    def _test_gen():
        yield 1

    assert check.generator_param(_test_gen(), "gen")

    gen = _test_gen()
    assert check.generator(gen)
    assert list(gen) == [1]
    assert check.generator(gen)
    assert list(gen) == []

    with pytest.raises(ParameterCheckError):
        assert check.generator_param(list(gen), "gen")

    with pytest.raises(ParameterCheckError):
        assert check.generator_param(None, "gen")

    with pytest.raises(ParameterCheckError):
        assert check.generator_param(_test_gen, "gen")


def test_opt_generator_param():
    def _test_gen():
        yield 1

    assert check.opt_generator_param(_test_gen(), "gen")

    assert check.opt_generator_param(None, "gen") is None

    with pytest.raises(ParameterCheckError):
        assert check.opt_generator_param(_test_gen, "gen")


def test_generator():
    def _test_gen():
        yield 1

    assert check.generator(_test_gen())

    gen = _test_gen()
    assert check.generator(gen)

    with pytest.raises(ParameterCheckError):
        assert check.generator(list(gen))

    with pytest.raises(ParameterCheckError):
        assert check.generator(None)

    with pytest.raises(ParameterCheckError):
        assert check.generator(_test_gen)


def test_opt_generator():
    def _test_gen():
        yield 1

    assert check.opt_generator(_test_gen())

    gen = _test_gen()
    assert check.opt_generator(gen)
    assert check.opt_generator(None) is None

    with pytest.raises(ParameterCheckError):
        assert check.opt_generator(list(gen))

    with pytest.raises(ParameterCheckError):
        assert check.opt_generator(_test_gen)


def test_internals():
    with pytest.raises(CheckError):
        check._check_key_value_types(None, str, str)  # pylint: disable=protected-access
