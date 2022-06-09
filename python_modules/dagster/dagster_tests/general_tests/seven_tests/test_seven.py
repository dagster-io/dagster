import inspect
import json
import sys
import tempfile
from functools import update_wrapper
from typing import List

import pytest

from dagster import DagsterType, seven
from dagster.core.types.dagster_type import ListType
from dagster.seven import is_subclass
from dagster.utils import file_relative_path


def test_is_ascii():
    assert seven.is_ascii("Hello!")
    assert not seven.is_ascii("您好！")


def test_import_module_from_path():
    foo_module = seven.import_module_from_path(
        "foo_module", file_relative_path(__file__, "foo_module.py")
    )
    assert foo_module.FOO == 7


def test_json_decode_error():
    with pytest.raises(seven.json.JSONDecodeError):
        json.loads(",dsfjd")


def test_json_dump():
    with tempfile.TemporaryFile("w+") as fd:
        seven.json.dump({"foo": "bar", "a": "b"}, fd)
        fd.seek(0)
        assert fd.read() == '{"a": "b", "foo": "bar"}'


def test_json_dumps():
    assert seven.json.dumps({"foo": "bar", "a": "b"}) == '{"a": "b", "foo": "bar"}'


def test_tempdir():
    assert not seven.temp_dir.get_system_temp_directory().startswith("/var")


def test_get_arg_names():
    def foo(one, two=2, three=None):  # pylint: disable=unused-argument
        pass

    assert len(seven.get_arg_names(foo)) == 3
    assert "one" in seven.get_arg_names(foo)
    assert "two" in seven.get_arg_names(foo)
    assert "three" in seven.get_arg_names(foo)


def test_is_lambda():
    foo = lambda: None

    def bar():
        pass

    baz = 3

    class Oof:
        test = lambda x: x

    assert seven.is_lambda(foo) == True
    assert seven.is_lambda(Oof.test) == True
    assert seven.is_lambda(bar) == False
    assert seven.is_lambda(baz) == False


def test_is_fn_or_decor_inst():
    class Quux:
        pass

    def foo():
        return Quux()

    bar = lambda _: Quux()

    baz = Quux()

    def quux_decor(fn):
        q = Quux()
        return update_wrapper(q, fn)

    @quux_decor
    def yoodles():
        pass

    assert seven.is_function_or_decorator_instance_of(foo, Quux) == True
    assert seven.is_function_or_decorator_instance_of(bar, Quux) == True
    assert seven.is_function_or_decorator_instance_of(baz, Quux) == False
    assert seven.is_function_or_decorator_instance_of(yoodles, Quux) == True


class Foo:
    pass


class Bar(Foo):
    pass


def test_is_subclass():
    assert is_subclass(Bar, Foo)
    assert not is_subclass(Foo, Bar)

    assert is_subclass(DagsterType, DagsterType)
    assert is_subclass(str, str)
    assert is_subclass(ListType, DagsterType)
    assert not is_subclass(DagsterType, ListType)
    assert not is_subclass(ListType, str)

    # type that aren't classes can be passed into is_subclass
    assert not inspect.isclass(List[str])
    assert not is_subclass(List[str], DagsterType)


@pytest.mark.skipif(
    sys.version_info.minor < 9, reason="Generic aliases only exist on py39 or later"
)
def test_is_subclass_generic_alias():
    # See comments around is_subclass for why this fails
    with pytest.raises(TypeError):
        issubclass(list[str], DagsterType)

    assert not is_subclass(list[str], DagsterType)
