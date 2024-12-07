import os

import pytest
from dagster_components.core.templated_param_resolver import TemplatedParamResolver
from jinja2 import UndefinedError


def resolver_with_os_environ_as_env() -> TemplatedParamResolver:
    def _env(key: str) -> str:
        return os.environ[key]

    return TemplatedParamResolver({"env": _env})


def test_basic_evaluation() -> None:
    assert TemplatedParamResolver({}).resolve("foo") == "foo"
    assert TemplatedParamResolver({"foo": "bar"}).resolve("{{ foo }}") == "bar"

    def func() -> str:
        return "from_func"

    assert TemplatedParamResolver({"func": func}).resolve("{{ func() }}") == "from_func"

    assert (
        TemplatedParamResolver({"dot_syntax": {"foo": "bar"}}).resolve("{{ dot_syntax.foo }}")
        == "bar"
    )


def test_default_os_environ_disallowed() -> None:
    with pytest.raises(UndefinedError):
        try:
            os.environ["TEST_ENV"] = "test_value"
            assert (
                TemplatedParamResolver({}).resolve("{{ os.environ['TEST_ENV'] }}") == "test_value"
            )
        finally:
            del os.environ["TEST_ENV"]

    try:
        os.environ["TEST_ENV"] = "test_value"
        resolver = resolver_with_os_environ_as_env()
        assert resolver.resolve("{{ env('TEST_ENV') }}") == "test_value"
    finally:
        del os.environ["TEST_ENV"]
