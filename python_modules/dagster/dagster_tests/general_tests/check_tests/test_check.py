# ruff: noqa: UP006, UP035
#
import collections.abc
import re
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Annotated,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Set,
    TypedDict,
    TypeVar,
    Union,
)

import dagster._check as check
import pytest
from dagster._annotations import PublicAttr
from dagster._check import (
    CheckError,
    ElementCheckError,
    EvalContext,
    ImportFrom,
    NotImplementedCheckError,
    ParameterCheckError,
    build_check_call_str,
)
from dagster._record import record

if TYPE_CHECKING:
    from dagster._core.test_utils import TestType  # used in lazy import ForwardRef test case


@contextmanager
def raises_with_message(exc_type, message_text):
    with pytest.raises(exc_type) as exc_info:
        yield

    assert str(exc_info.value) == message_text


def is_python_three():
    return sys.version_info[0] >= 3


# ###################################################################################################
# ##### TYPE CHECKS
# ###################################################################################################

# ########################
# ##### BOOL
# ########################


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


def test_bool_elem():
    ddict = {"a_true": True, "a_str": "a", "a_num": 1, "a_none": None}

    assert check.bool_elem(ddict, "a_true") is True

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, "a_none")

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, "a_num")

    with pytest.raises(ElementCheckError):
        check.bool_elem(ddict, "a_str")


# ########################
# ##### CALLABLE
# ########################


def test_callable_param():
    lamb = lambda: 1
    assert check.callable_param(lamb, "lamb") == lamb

    with pytest.raises(ParameterCheckError):
        check.callable_param(None, "lamb")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.callable_param(2, "lamb")  # pyright: ignore[reportArgumentType]


def test_opt_callable_param():
    lamb = lambda: 1
    assert check.opt_callable_param(lamb, "lamb") == lamb
    assert check.opt_callable_param(None, "lamb") is None
    assert check.opt_callable_param(None, "lamb") is None
    assert check.opt_callable_param(None, "lamb", default=lamb) == lamb

    with pytest.raises(ParameterCheckError):
        check.opt_callable_param(2, "lamb")  # pyright: ignore[reportCallIssue,reportArgumentType]


def test_is_callable():
    def fn():
        pass

    assert check.is_callable(fn) == fn
    assert check.is_callable(lambda: None)
    assert check.is_callable(lambda: None, "some desc")

    with pytest.raises(CheckError):
        check.is_callable(None)  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        check.is_callable(1)  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError, match="some other desc"):
        check.is_callable(1, "some other desc")  # pyright: ignore[reportArgumentType]


# ########################
# ##### CLASS
# ########################


def test_opt_class_param():
    class Foo:
        pass

    assert check.opt_class_param(int, "foo")
    assert check.opt_class_param(Foo, "foo")

    assert check.opt_class_param(None, "foo") is None
    assert check.opt_class_param(None, "foo", Foo) is Foo

    with pytest.raises(CheckError):
        check.opt_class_param(check, "foo")

    with pytest.raises(CheckError):
        check.opt_class_param(234, "foo")

    with pytest.raises(CheckError):
        check.opt_class_param("bar", "foo")

    with pytest.raises(CheckError):
        check.opt_class_param(Foo(), "foo")


def test_class_param():
    class Bar:
        pass

    assert check.class_param(int, "foo")
    assert check.class_param(Bar, "foo")

    with pytest.raises(CheckError):
        check.class_param(None, "foo")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        check.class_param(check, "foo")

    with pytest.raises(CheckError):
        check.class_param(234, "foo")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        check.class_param("bar", "foo")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        check.class_param(Bar(), "foo")  # pyright: ignore[reportArgumentType]

    class Super:
        pass

    class Sub(Super):
        pass

    class Alone:
        pass

    assert check.class_param(Sub, "foo", superclass=Super)

    with pytest.raises(CheckError):
        assert check.class_param(Alone, "foo", superclass=Super)

    with pytest.raises(CheckError):
        assert check.class_param("value", "foo", superclass=Super)  # pyright: ignore[reportArgumentType]

    assert check.opt_class_param(Sub, "foo", superclass=Super)
    assert check.opt_class_param(None, "foo", superclass=Super) is None

    with pytest.raises(CheckError):
        assert check.opt_class_param(Alone, "foo", superclass=Super)

    with pytest.raises(CheckError):
        assert check.opt_class_param("value", "foo", superclass=Super)


# ########################
# ##### DICT
# ########################


class Wrong:
    pass


class AlsoWrong:
    pass


DICT_TEST_CASES = [
    (dict(obj={}), True),
    (dict(obj={"a": 2}), True),
    (dict(obj=None), False),
    (dict(obj=0), False),
    (dict(obj=1), False),
    (dict(obj="foo"), False),
    (dict(obj=["foo"]), False),
    (dict(obj=[]), False),
    (dict(obj={"str": 1}, key_type=str, value_type=int), True),
    (dict(obj={"str": 1}, value_type=int), True),
    (dict(obj={"str": 1}, key_type=str), True),
    (dict(obj={"str": 1}), True),
    (dict(obj={}, key_type=str, value_type=int), True),
    (dict(obj={}, value_type=int), True),
    (dict(obj={}, key_type=str), True),
    (dict(obj={}), True),
    (
        dict(
            obj={"str": 1, "str2": "str", 1: "str", 2: "str"},
            key_type=(str, int),
            value_type=(str, int),
        ),
        True,
    ),
    (dict(obj={"str": 1}, key_type=Wrong, value_type=Wrong), False),
    (dict(obj={"str": 1}, key_type=Wrong, value_type=int), False),
    (dict(obj={"str": 1}, key_type=str, value_type=Wrong), False),
    (dict(obj={"str": 1}, key_type=Wrong), False),
    (dict(obj={"str": 1}, key_type=(Wrong, AlsoWrong)), False),
    (dict(obj={"str": 1}, value_type=(Wrong, AlsoWrong)), False),
]


@pytest.mark.parametrize("kwargs, should_succeed", DICT_TEST_CASES)
def test_dict_param(kwargs, should_succeed):
    if should_succeed:
        assert check.dict_param(**kwargs, param_name="name") == kwargs["obj"]
    else:
        with pytest.raises(CheckError):
            check.dict_param(**kwargs, param_name="name")


@pytest.mark.parametrize("kwargs, should_succeed", DICT_TEST_CASES)
def test_is_dict(kwargs, should_succeed):
    if should_succeed:
        assert check.is_dict(**kwargs) == kwargs["obj"]
    else:
        with pytest.raises(CheckError):
            check.is_dict(**kwargs)


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
    ddict = {"a": 2}
    assert check.opt_dict_param(ddict, "opt_dict_param") == ddict

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(0, "opt_dict_param")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(1, "opt_dict_param")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param("foo", "opt_dict_param")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param(["foo"], "opt_dict_param")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.opt_dict_param([], "opt_dict_param")  # pyright: ignore[reportArgumentType]


def test_opt_nullable_dict_param():
    assert check.opt_nullable_dict_param(None, "opt_nullable_dict_param") is None
    assert check.opt_nullable_dict_param({}, "opt_nullable_dict_param") == {}
    ddict = {"a": 2}
    assert check.opt_nullable_dict_param(ddict, "opt_nullable_dict_param") == ddict

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_dict_param(1, "opt_nullable_dict_param")

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_dict_param("foo", "opt_nullable_dict_param")


def test_opt_two_dim_dict_param():
    assert check.opt_two_dim_dict_param({}, "foo") == {}
    assert check.opt_two_dim_dict_param({"key": {}}, "foo")
    assert check.opt_two_dim_dict_param({"key": {"key2": 2}}, "foo")
    assert check.opt_two_dim_dict_param(None, "foo") == {}

    with pytest.raises(CheckError):
        assert check.opt_two_dim_dict_param("str", "foo")


def test_two_dim_dict():
    assert check.two_dim_dict_param({}, "foo") == {}
    assert check.two_dim_dict_param({"key": {}}, "foo")
    assert check.two_dim_dict_param({"key": {"key2": 2}}, "foo")

    # make sure default dict passes
    default_dict = defaultdict(dict)
    default_dict["key"]["key2"] = 2
    assert check.two_dim_dict_param(default_dict, "foo")

    with raises_with_message(
        CheckError, """Param "foo" is not a dict. Got None which is type <class 'NoneType'>."""
    ):
        check.two_dim_dict_param(None, "foo")

    with raises_with_message(
        CheckError,
        "Value in dict mismatches expected type for key int_value. Expected value "
        "of type <class 'dict'>. Got value 2 of type <class 'int'>.",
    ):
        check.two_dim_dict_param({"int_value": 2}, "foo")

    with raises_with_message(
        CheckError,
        "Value in dict mismatches expected type for key level_two_value_mismatch. "
        "Expected value of type <class 'str'>. Got value 2 of type <class 'int'>.",
    ):
        check.two_dim_dict_param(
            {"level_one_key": {"level_two_value_mismatch": 2}}, "foo", value_type=str
        )

    with raises_with_message(
        CheckError,
        (
            "Key in dict mismatches type. Expected <class 'int'>. Got 'key'"
            if is_python_three()
            else "Key in dictionary mismatches type. Expected <type 'int'>. Got 'key'"
        ),
    ):
        assert check.two_dim_dict_param({"key": {}}, "foo", key_type=int)

    with raises_with_message(
        CheckError,
        (
            "Key in dict mismatches type. Expected <class 'int'>. Got 'level_two_key'"
            if is_python_three()
            else "Key in dictionary mismatches type. Expected <type 'int'>. Got 'level_two_key'"
        ),
    ):
        assert check.two_dim_dict_param({1: {"level_two_key": "something"}}, "foo", key_type=int)


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

    assert check.dict_elem(
        {"foo": {"str": 1, "str2": "str", 1: "str", 2: "str"}},
        "foo",
        key_type=(str, int),
        value_type=(str, int),
    )


def test_opt_dict_elem():
    dict_value = {"blah": "blahblah"}
    ddict = {"dictkey": dict_value, "stringkey": "A", "nonekey": None}

    assert check.opt_dict_elem(ddict, "dictkey") == dict_value
    assert check.opt_dict_elem(ddict, "dictkey", key_type=str, value_type=str) == dict_value
    assert check.opt_dict_elem(ddict, "nonekey") == {}
    assert check.opt_dict_elem(ddict, "nonexistantkey") == {}

    with pytest.raises(CheckError):
        check.opt_dict_elem(ddict, "stringkey")

    with pytest.raises(CheckError):
        check.opt_dict_elem(ddict, "dictkey", key_type=str, value_type=int)


# ########################
# ##### FLOAT
# ########################


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

    assert check.opt_float_elem(ddict, "a_none") is None

    assert check.opt_float_elem(ddict, "nonexistentkey") is None

    with pytest.raises(ElementCheckError):
        check.opt_float_elem(ddict, "a_bool")

    with pytest.raises(ElementCheckError):
        check.opt_float_elem(ddict, "a_int")

    with pytest.raises(ElementCheckError):
        check.opt_float_elem(ddict, "a_str")


# ########################
# ##### GENERATOR
# ########################


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
        assert check.generator_param(list(gen), "gen")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        assert check.generator_param(None, "gen")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        assert check.generator_param(_test_gen, "gen")  # pyright: ignore[reportArgumentType]


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


# ########################
# ##### INT
# ########################


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


def test_int_elem():
    ddict = {"a_bool": True, "a_float": 1.0, "a_int": 1, "a_none": None, "a_str": "a"}

    assert check.int_elem(ddict, "a_int") == 1

    assert check.int_elem(ddict, "a_bool") is True

    with pytest.raises(ElementCheckError):
        check.int_elem(ddict, "a_float")

    with pytest.raises(ElementCheckError):
        check.int_elem(ddict, "a_none")

    with pytest.raises(ElementCheckError):
        check.int_elem(ddict, "a_str")


def test_opt_int_elem():
    ddict = {"a_bool": True, "a_float": 1.0, "a_int": 1, "a_none": None, "a_str": "a"}

    assert check.opt_int_elem(ddict, "a_int") == 1

    assert check.opt_int_elem(ddict, "a_none") is None

    assert check.opt_int_elem(ddict, "nonexistentkey") is None

    assert check.opt_int_elem(ddict, "a_bool") is True

    with pytest.raises(ElementCheckError):
        check.opt_int_elem(ddict, "a_float")

    with pytest.raises(ElementCheckError):
        check.opt_int_elem(ddict, "a_str")


# ########################
# ##### INST
# ########################


def test_inst():
    class Foo:
        pass

    class Bar:
        pass

    obj = Foo()

    assert check.inst(obj, Foo) == obj

    with pytest.raises(CheckError, match="not a Bar"):
        check.inst(Foo(), Bar)

    with pytest.raises(CheckError, match="Expected only a Bar"):
        check.inst(Foo(), Bar, "Expected only a Bar")

    with pytest.raises(CheckError, match=re.escape("not one of ['Bar', 'Foo']")):
        check.inst(1, (Foo, Bar))

    with pytest.raises(CheckError, match=re.escape("not one of ['Bar', 'Foo']")):
        check.inst(1, (Foo, Bar), additional_message="a desc")

    with pytest.raises(CheckError, match=re.escape("a desc")):
        check.inst(1, (Foo, Bar), additional_message="a desc")


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


# ########################
# ##### LIST
# ########################


def test_list_param():
    assert check.list_param([], "list_param") == []

    assert check.list_param(["foo"], "list_param", of_type=str) == ["foo"]

    with pytest.raises(ParameterCheckError):
        check.list_param(None, "list_param")

    with pytest.raises(ParameterCheckError):
        check.list_param("3u4", "list_param")

    with pytest.raises(CheckError):
        check.list_param(["foo"], "list_param", of_type=int)


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


def test_opt_list_param():
    assert check.opt_list_param(None, "list_param") == []
    assert check.opt_list_param(None, "list_param", of_type=str) == []
    assert check.opt_list_param([], "list_param") == []
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


def test_opt_nullable_list_param():
    assert check.opt_nullable_list_param(None, "list_param") is None
    assert check.opt_nullable_list_param([], "list_param") == []
    obj_list = [1]
    assert check.opt_nullable_list_param(obj_list, "list_param") == obj_list

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_list_param(0, "list_param")  # pyright: ignore[reportCallIssue,reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_list_param("", "list_param")  # pyright: ignore[reportCallIssue,reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.opt_nullable_list_param("3u4", "list_param")  # pyright: ignore[reportCallIssue,reportArgumentType]


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


def test_two_dim_list_param():
    assert check.two_dim_list_param([[1, 2], [2, 3]], "something")

    with pytest.raises(CheckError):
        assert check.two_dim_list_param(None, "something")

    with pytest.raises(CheckError):
        assert check.two_dim_list_param([1, 2, 4], "something")

    with pytest.raises(CheckError):
        assert check.two_dim_list_param([], "something")

    with pytest.raises(CheckError):
        assert check.two_dim_list_param([[1, 2], 3], "soemthing")

    with pytest.raises(CheckError):
        assert check.two_dim_list_param([[1, 2], [3.0, 4.1]], "something", of_type=int)

    with pytest.raises(CheckError):
        assert check.two_dim_list_param([[1, 2], [2, 3, 4]], "something")


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


# ########################
# ##### MAPPING
# ########################


class SimpleMapping(collections.abc.Mapping):
    def __init__(self, **kwargs):
        self._dict = dict()
        for key, value in kwargs.items():
            self._dict[key] = value

    def __getitem__(self, key):
        return self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)


MAPPING_TEST_CASES = DICT_TEST_CASES + [
    (dict(obj=SimpleMapping(x=1), key_type=str, value_type=int), True),
]


@pytest.mark.parametrize("kwargs, should_succeed", MAPPING_TEST_CASES)
def test_mapping_param(kwargs, should_succeed):
    if should_succeed:
        assert check.mapping_param(**kwargs, param_name="name") == kwargs["obj"]
    else:
        with pytest.raises(CheckError):
            check.mapping_param(**kwargs, param_name="name")


def test_opt_mapping_param():
    mapping = SimpleMapping(x=1)
    assert check.opt_mapping_param(mapping, param_name="name") == mapping
    assert check.opt_mapping_param(mapping, param_name="name", key_type=str) == mapping
    assert check.opt_mapping_param(mapping, param_name="name", value_type=int) == mapping
    assert check.opt_mapping_param(None, param_name="name") == dict()

    with pytest.raises(CheckError):
        check.opt_mapping_param("foo", param_name="name")  # pyright: ignore[reportArgumentType]
    assert check.opt_nullable_mapping_param(None, "name") is None


# ########################
# ##### NOT NONE
# ########################


def test_not_none_param():
    assert check.not_none_param(1, "fine")
    check.not_none_param(0, "zero is fine")
    check.not_none_param("", "empty str is fine")

    with pytest.raises(CheckError):
        check.not_none_param(None, "none fails")


# ########################
# ##### PATH
# ########################


def test_path_param():
    from pathlib import Path

    assert check.path_param("/a/b.csv", "path_param") == "/a/b.csv"
    if sys.platform.startswith("win32"):
        assert check.opt_path_param(Path("c:\\a\\b.csv"), "path_param") == "c:\\a\\b.csv"
    else:
        assert check.opt_path_param(Path("/a/b.csv"), "path_param") == "/a/b.csv"

    with pytest.raises(ParameterCheckError):
        check.path_param(None, "path_param")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.path_param(0, "path_param")  # pyright: ignore[reportArgumentType]


def test_opt_path_param():
    from pathlib import Path

    assert check.opt_path_param("/a/b.csv", "path_param") == "/a/b.csv"
    if sys.platform.startswith("win32"):
        assert check.opt_path_param(Path("c:\\a\\b.csv"), "path_param") == "c:\\a\\b.csv"
    else:
        assert check.opt_path_param(Path("/a/b.csv"), "path_param") == "/a/b.csv"
    assert check.opt_path_param(None, "path_param") is None

    with pytest.raises(ParameterCheckError):
        check.opt_path_param(0, "path_param")  # pyright: ignore[reportCallIssue,reportArgumentType]


# ########################
# ##### SET
# ########################


def test_set_param():
    assert check.set_param(set(), "set_param") == set()
    assert check.set_param(frozenset(), "set_param") == set()

    with pytest.raises(ParameterCheckError):
        check.set_param(None, "set_param")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.set_param("3u4", "set_param")  # pyright: ignore[reportArgumentType]

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


def test_opt_set_param():
    assert check.opt_set_param(None, "set_param") == set()
    assert check.opt_set_param(set(), "set_param") == set()
    assert check.opt_set_param(frozenset(), "set_param") == set()
    assert check.opt_set_param({3}, "set_param") == {3}

    with pytest.raises(ParameterCheckError):
        check.opt_set_param(0, "set_param")  # pyright: ignore[reportArgumentType]

    with pytest.raises(ParameterCheckError):
        check.opt_set_param("3u4", "set_param")  # pyright: ignore[reportArgumentType]


# ########################
# ##### SEQUENCE
# ########################


@record
class SomeRecord: ...


def test_sequence_param():
    assert check.sequence_param([], "sequence_param") == []
    assert check.sequence_param(tuple(), "sequence_param") == tuple()

    assert check.sequence_param(["foo"], "sequence_param", of_type=str) == ["foo"]

    with pytest.raises(ParameterCheckError):
        check.sequence_param(None, "sequence_param")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        check.sequence_param(1, "sequence_param", of_type=int)  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        check.sequence_param(["foo"], "sequence_param", of_type=int)

    with pytest.raises(CheckError):
        check.sequence_param("foo", "sequence_param")

    with pytest.raises(CheckError, match="str is a disallowed Sequence type"):
        check.sequence_param("foo", "sequence_param", of_type=str)

    with pytest.raises(CheckError):
        check.sequence_param(SomeRecord(), "sequence_param")  # pyright: ignore[reportArgumentType]


def test_opt_sequence_param():
    assert check.opt_sequence_param([], "sequence_param") == []
    assert check.opt_sequence_param(tuple(), "sequence_param") == tuple()

    assert check.opt_sequence_param(["foo"], "sequence_param", of_type=str) == ["foo"]

    assert check.opt_sequence_param(None, "sequence_param") == []

    with pytest.raises(CheckError):
        check.opt_sequence_param(1, "sequence_param", of_type=int)  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        check.opt_sequence_param(["foo"], "sequence_param", of_type=int)

    with pytest.raises(CheckError):
        check.opt_sequence_param("foo", "sequence_param")

    with pytest.raises(CheckError, match="str is a disallowed Sequence type"):
        check.opt_sequence_param("foo", "sequence_param", of_type=str)

    with pytest.raises(CheckError):
        check.opt_sequence_param(SomeRecord(), "sequence_param")  # pyright: ignore[reportArgumentType]


def test_opt_nullable_sequence_param():
    assert check.opt_nullable_sequence_param([], "sequence_param") == []
    assert check.opt_nullable_sequence_param(tuple(), "sequence_param") == tuple()

    assert check.opt_nullable_sequence_param(["foo"], "sequence_param", of_type=str) == ["foo"]

    assert check.opt_nullable_sequence_param(None, "sequence_param") is None

    with pytest.raises(CheckError):
        check.opt_nullable_sequence_param(1, "sequence_param", of_type=int)  # pyright: ignore[reportCallIssue,reportArgumentType]

    with pytest.raises(CheckError):
        check.opt_nullable_sequence_param(["foo"], "sequence_param", of_type=int)

    with pytest.raises(CheckError, match="str is a disallowed Sequence type"):
        assert check.opt_nullable_sequence_param("foo", "sequence_param", of_type=str)

    with pytest.raises(CheckError):
        check.opt_nullable_sequence_param(SomeRecord(), "sequence_param")  # pyright: ignore[reportCallIssue,reportArgumentType]


# ########################
# ##### STR
# ########################


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

    assert check.opt_str_elem(ddict, "a_none") is None

    assert check.opt_str_elem(ddict, "nonexistentkey") is None

    with pytest.raises(ElementCheckError):
        check.opt_str_elem(ddict, "a_num")


# ########################
# ##### TUPLE
# ########################


def test_tuple_param():
    assert check.tuple_param((1, 2), "something")

    with pytest.raises(CheckError):
        assert check.tuple_param(None, "something")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        assert check.tuple_param(1, "something")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        assert check.tuple_param([1], "something")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        assert check.tuple_param({1: 2}, "something")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError):
        assert check.tuple_param("kdjfkd", "something")  # pyright: ignore[reportArgumentType]

    assert check.tuple_param((3, 4), "something", of_type=int)
    assert check.tuple_param(("foo", "bar"), "something", of_type=str)

    assert check.tuple_param((3, 4), "something", of_type=(int,))
    assert check.tuple_param((3, 4), "something", of_type=(int, str))
    assert check.tuple_param((3, "bar"), "something", of_type=(int, str))

    with pytest.raises(CheckError):
        check.tuple_param((3, 4, 5), "something", of_type=str)

    with pytest.raises(CheckError):
        check.tuple_param((3, 4), "something", of_type=(str,))

    assert check.tuple_param((3, "a"), "something", of_shape=(int, str))

    with pytest.raises(CheckError):
        check.tuple_param((3, "a"), "something", of_shape=(int, str, int))

    with pytest.raises(CheckError):
        check.tuple_param((3, "a"), "something", of_shape=(str, int))

    with pytest.raises(CheckError):
        check.is_tuple((3, 4), of_shape=(int, int), of_type=int)


def test_opt_tuple_param():
    assert check.opt_tuple_param((1, 2), "something")
    assert check.opt_tuple_param(None, "something") == tuple()

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

    assert check.opt_tuple_param((3, 4), "something", of_type=(int,))
    assert check.opt_tuple_param((3, 4), "something", of_type=(int, str))
    assert check.opt_tuple_param((3, "bar"), "something", of_type=(int, str))

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, 4, 5), "something", of_type=str)

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, 4), "something", of_type=(str,))

    assert check.opt_tuple_param((3, "a"), "something", of_shape=(int, str))

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, "a"), "something", of_shape=(int, str, int))

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, "a"), "something", of_shape=(str, int))

    with pytest.raises(CheckError):
        check.opt_tuple_param((3, 4), "something", of_shape=(int, int), of_type=int)


def test_opt_nullable_tuple_param():
    assert check.opt_nullable_tuple_param((1, 2), "something")
    assert check.opt_nullable_tuple_param(None, "something") is None

    with pytest.raises(CheckError):
        check.opt_nullable_tuple_param([3, 4], "something", of_shape=(int, int), of_type=int)  # pyright: ignore[reportCallIssue,reportArgumentType]


def test_is_tuple():
    assert check.is_tuple(()) == ()

    with pytest.raises(CheckError):
        check.is_tuple(None)

    with pytest.raises(CheckError):
        check.is_tuple("3u4")

    with pytest.raises(CheckError, match="Did you pass a class"):
        check.is_tuple((str,), of_type=int)

    with pytest.raises(CheckError):
        check.is_tuple(SomeRecord())


def test_tuple_elem():
    tuple_value = ("blah", "blahblah")
    ddict = {"tuplekey": tuple_value, "stringkey": "A", "nonekey": None, "reckey": SomeRecord()}

    assert check.tuple_elem(ddict, "tuplekey") == tuple_value
    assert check.tuple_elem(ddict, "tuplekey", of_type=str) == tuple_value

    with pytest.raises(CheckError):
        check.tuple_elem(ddict, "nonekey")

    with pytest.raises(CheckError):
        check.tuple_elem(ddict, "nonexistantkey")

    with pytest.raises(CheckError):
        check.tuple_elem(ddict, "stringkey")

    with pytest.raises(CheckError):
        check.tuple_elem(ddict, "tuplekey", of_type=int)

    with pytest.raises(CheckError):
        check.tuple_elem(ddict, "reckey")


def test_opt_tuple_elem():
    tuple_value = ("blah", "blahblah")
    ddict = {"tuplekey": tuple_value, "stringkey": "A", "nonekey": None, "reckey": SomeRecord()}

    assert check.opt_tuple_elem(ddict, "tuplekey") == tuple_value
    assert check.opt_tuple_elem(ddict, "tuplekey", of_type=str) == tuple_value
    assert check.opt_tuple_elem(ddict, "nonekey") == tuple()
    assert check.opt_tuple_elem(ddict, "nonexistantkey") == tuple()

    with pytest.raises(CheckError):
        check.opt_tuple_elem(ddict, "stringkey")

    with pytest.raises(CheckError):
        check.opt_tuple_elem(ddict, "tuplekey", of_type=int)

    with pytest.raises(CheckError):
        check.opt_tuple_elem(ddict, "reckey")


def test_typed_is_tuple():
    class Foo:
        pass

    class Bar:
        pass

    assert check.is_tuple((), Foo) == ()
    foo_tuple = (Foo(),)
    assert check.is_tuple(foo_tuple, Foo) == foo_tuple
    assert check.is_tuple(foo_tuple, (Foo, Bar))

    with pytest.raises(CheckError):
        check.is_tuple((Bar(),), Foo)

    with pytest.raises(CheckError):
        check.is_tuple((None,), Foo)

    assert check.is_tuple((Foo(), Bar()), of_shape=(Foo, Bar))

    with pytest.raises(CheckError):
        check.is_tuple((Foo(),), of_shape=(Foo, Bar))

    with pytest.raises(CheckError):
        check.is_tuple((Foo(), Foo()), of_shape=(Foo, Bar))

    with pytest.raises(CheckError):
        check.is_tuple((Foo(), Foo()), of_shape=(Foo, Foo), of_type=Foo)


# ###################################################################################################
# ##### OTHER CHECKS
# ###################################################################################################


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
        check.failed(0)  # pyright: ignore[reportArgumentType]


def test_not_implemented():
    with pytest.raises(NotImplementedCheckError, match="some string"):
        check.not_implemented("some string")

    with pytest.raises(CheckError, match="desc argument must be a string"):
        check.not_implemented(None)  # pyright: ignore[reportArgumentType]


def test_iterable():
    assert check.iterable_param([], "thisisfine") == []
    assert check.iterable_param([1], "thisisfine") == [1]
    assert check.iterable_param([1], "thisisfine", of_type=int) == [1]
    assert check.iterable_param((i for i in [1, 2]), "thisisfine")
    # assert that it does not coerce generator to list
    assert check.iterable_param((i for i in [1, 2]), "thisisfine") != [1, 2]
    assert list(check.iterable_param((i for i in [1, 2]), "thisisfine")) == [1, 2]

    with pytest.raises(CheckError, match="Iterable.*str"):
        check.iterable_param("lkjsdkf", "stringisiterable")

    with pytest.raises(CheckError, match="Iterable.*None"):
        check.iterable_param(None, "nonenotallowed")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError, match="Iterable.*int"):
        check.iterable_param(1, "intnotallowed")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError, match="Member of iterable mismatches type"):
        check.iterable_param([1], "typemismatch", of_type=str)

    with pytest.raises(CheckError, match="Member of iterable mismatches type"):
        check.iterable_param(["atr", 2], "typemismatchmixed", of_type=str)

    with pytest.raises(CheckError, match="Member of iterable mismatches type"):
        check.iterable_param(["atr", None], "nonedoesntcount", of_type=str)

    with pytest.raises(CheckError):
        check.iterable_param(SomeRecord(), "nonenotallowed")  # pyright: ignore[reportArgumentType]


def test_opt_iterable():
    assert check.opt_iterable_param(None, "thisisfine") == []
    assert check.opt_iterable_param([], "thisisfine") == []
    assert check.opt_iterable_param([1], "thisisfine") == [1]
    assert check.opt_iterable_param((i for i in [1, 2]), "thisisfine")
    # assert that it does not coerce generator to list
    assert check.opt_iterable_param((i for i in [1, 2]), "thisisfine") != [1, 2]
    # not_none coerces to Iterable[T] so
    assert list(check.not_none(check.opt_iterable_param((i for i in [1, 2]), "thisisfine"))) == [
        1,
        2,
    ]

    check.opt_iterable_param(None, "noneisallowed")

    with pytest.raises(CheckError, match="Iterable.*str"):
        check.opt_iterable_param("lkjsdkf", "stringisiterable")

    with pytest.raises(CheckError, match="Iterable.*int"):
        check.opt_iterable_param(1, "intnotallowed")  # pyright: ignore[reportArgumentType]

    with pytest.raises(CheckError, match="Member of iterable mismatches type"):
        check.opt_iterable_param([1], "typemismatch", of_type=str)

    with pytest.raises(CheckError, match="Member of iterable mismatches type"):
        check.opt_iterable_param(["atr", 2], "typemismatchmixed", of_type=str)

    with pytest.raises(CheckError, match="Member of iterable mismatches type"):
        check.opt_iterable_param(["atr", None], "nonedoesntcount", of_type=str)

    with pytest.raises(CheckError):
        check.opt_iterable_param(SomeRecord(), "nonenotallowed")  # pyright: ignore[reportArgumentType]


def test_is_iterable() -> None:
    assert check.is_iterable([]) == []
    assert check.is_iterable((1, 2)) == tuple([1, 2])
    assert check.is_iterable("foo") == "foo"  # str is iterable
    assert check.is_iterable({"a": 1}) == {"a": 1}  # dict is iterable

    assert check.is_iterable([1, "str"]) == [1, "str"]

    with pytest.raises(CheckError):
        check.is_iterable([1, "str"], of_type=int)

    with pytest.raises(CheckError):
        check.is_iterable([1, "str"], of_type=str)

    with pytest.raises(CheckError):
        check.is_iterable(None)

    with pytest.raises(CheckError):
        check.is_iterable(1)


def test_is_iterable_typing() -> None:
    def returns_iterable_of_int_but_typed_any() -> Any:
        return [1, 2]

    def returns_iterable_of_t() -> Iterable[int]:
        any_typed = returns_iterable_of_int_but_typed_any()
        retval = check.is_iterable(any_typed, of_type=str)
        # That the type: ignore is necessary is proof that
        # is_iterable flows type information correctly
        return retval  # type: ignore

    # meaningless assert. The test is show the typechecker working
    assert returns_iterable_of_t


# ###################################################################################################
# ##### CHECK BUILDER
# ###################################################################################################


def build_check_call(ttype, name, eval_ctx: EvalContext):
    body = build_check_call_str(ttype, name, eval_ctx)
    lazy_import_str = "\n    ".join(
        f"from {module} import {t}" for t, module in eval_ctx.lazy_imports.items()
    )

    fn = f"""
def _check({name}):
    {lazy_import_str}
    return {body}
"""
    return eval_ctx.compile_fn(fn, "_check")


class Foo: ...


class SubFoo(Foo): ...


class Bar: ...


T = TypeVar("T")


class Gen(Generic[T]): ...


class SubGen(Gen[str]): ...


class MyTypedDict(TypedDict):
    foo: str
    bar: str


BUILD_CASES = [
    (int, [4], ["4"]),
    (float, [4.2], ["4.1"]),
    (str, ["hi"], [Foo()]),
    (Bar, [Bar()], [Foo()]),
    (Optional[Bar], [Bar()], [Foo()]),
    (List[str], [["a", "b"]], [[1, 2]]),
    (Sequence[str], [["a", "b"]], [[1, 2], "just_a_string"]),
    (Iterable[str], [["a", "b"]], [[1, 2]]),
    (Set[str], [{"a", "b"}], [{1, 2}]),
    (AbstractSet[str], [{"a", "b"}], [{1, 2}]),
    (Optional[AbstractSet[str]], [{"a", "b"}, None], [{1, 2}]),
    (
        Mapping[str, AbstractSet[str]],
        [
            {"letters": {"a", "b"}},
            # should fail, but we do not yet handle inner collection types,
            # check.mapping_param(..., key_type=str, value_type=AbstractSet)
            {"numbers": {1, 2}},
        ],
        [
            {"letters": ["a", "b"]},
        ],
    ),
    (Dict[str, int], [{"a": 1}], [{1: "a"}]),
    (Mapping[str, int], [{"a": 1}], [{1: "a"}]),
    (Optional[int], [None], ["4"]),
    (Optional[Bar], [None], [Foo()]),
    (Optional[List[str]], [["a", "b"]], [[1, 2]]),
    (Optional[Sequence[str]], [["a", "b"]], [[1, 2]]),
    (Optional[Iterable[str]], [["a", "b"]], [[1, 2]]),
    (Optional[Set[str]], [{"a", "b"}], [{1, 2}]),
    (Optional[Dict[str, int]], [{"a": 1}], [{1: "a"}]),
    (Optional[Mapping[str, int]], [{"a": 1}], [{1: "a"}]),
    (PublicAttr[Optional[Mapping[str, int]]], [{"a": 1}], [{1: "a"}]),  # type: ignore  # ignored for update, fix me!
    (PublicAttr[Bar], [Bar()], [Foo()]),  # type: ignore  # ignored for update, fix me!
    (Annotated[Bar, None], [Bar()], [Foo()]),
    (Annotated["Bar", None], [Bar()], [Foo()]),
    (List[Annotated[Bar, None]], [[Bar()], []], [[Foo()]]),
    (
        List[Annotated["TestType", ImportFrom("dagster._core.test_utils")]],
        [[]],  # avoid importing TestType
        [[Foo()]],
    ),
    (Union[bool, Foo], [True], [None]),
    (Union[Foo, "Bar"], [Bar()], [None]),
    (TypeVar("T", bound=Foo), [Foo(), SubFoo()], [Bar()]),
    (TypeVar("T", bound=Optional[Foo]), [None], [Bar()]),
    (TypeVar("T"), [Foo(), None], []),
    (Literal["apple"], ["apple"], ["banana"]),
    (Literal["apple", "manzana"], ["apple", "manzana"], ["banana"]),
    (Callable, [lambda x: x, int], [4]),
    (Callable[[], int], [lambda x: x, int], [4]),
    # fwd refs
    ("Foo", [Foo()], [Bar()]),
    (Optional["Foo"], [Foo()], [Bar()]),
    (PublicAttr[Optional["Foo"]], [None], [Bar()]),  # type: ignore  # ignored for update, fix me!
    (Mapping[str, Optional["Foo"]], [{"foo": Foo()}], [{"bar": Bar()}]),
    (Mapping[str, Optional["Foo"]], [{"foo": Foo()}], [{"bar": Bar()}]),
    (Gen, [Gen()], [Bar()]),
    (Gen[str], [Gen()], [Bar()]),
    (SubGen, [SubGen()], [Bar()]),
    (Sequence[SubGen], [[SubGen()]], [[Bar()]]),
    (Sequence[Gen[str]], [[Gen()]], [[Bar()]]),
    (
        MyTypedDict,
        [
            {"foo": "f", "bar": "b"},
            {},  # cant actually validate TypeDict structure, just that its a dict
        ],
        [None, Foo()],
    ),
    (Optional[MyTypedDict], [{"foo": "f", "bar": "b"}, None], [Foo()]),
]


@pytest.mark.parametrize("ttype, should_succeed, should_fail", BUILD_CASES)
def test_build_check_call(
    ttype: type, should_succeed: Sequence[object], should_fail: Sequence[object]
) -> None:
    eval_ctx = EvalContext(globals(), locals(), {})
    check_call = build_check_call(ttype, "test_param", eval_ctx)

    for obj in should_succeed:
        check_call(obj)

    for obj in should_fail:
        with pytest.raises(CheckError):
            check_call(obj)


def test_build_check_errors() -> None:
    with pytest.raises(CheckError, match=r"Unable to resolve ForwardRef\('NoExist'\)"):
        build_check_call(
            List["NoExist"],  # type: ignore # noqa
            "bad",
            EvalContext(globals(), locals(), {}),
        )


def test_forward_ref_flow() -> None:
    # original context captured at decl
    eval_ctx = EvalContext(globals(), locals(), {})
    ttype = List["Late"]  # class not yet defined

    class Late: ...

    with pytest.raises(CheckError):
        # can not build call since ctx was captured before definition
        build_check_call(ttype, "ok", eval_ctx)

    eval_ctx.update_from_frame(0)  # update from callsite frame
    # now it works
    call = build_check_call(ttype, "ok", eval_ctx)
    call([Late()])
