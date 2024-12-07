import os

import pytest
from dagster_components.core.dsl_evaluator import DslEvaluator
from jinja2 import UndefinedError


def evaluator_with_os_environ_as_var() -> DslEvaluator:
    def _var(key: str) -> str:
        return os.environ[key]

    return DslEvaluator({"var": _var})


def test_basic_evaluation() -> None:
    assert DslEvaluator({}).eval("foo") == "foo"
    assert DslEvaluator({"foo": "bar"}).eval("{{ foo }}") == "bar"

    def func() -> str:
        return "from_func"

    assert DslEvaluator({"func": func}).eval("{{ func() }}") == "from_func"

    assert DslEvaluator({"dot_syntax": {"foo": "bar"}}).eval("{{ dot_syntax.foo }}") == "bar"


def test_default_os_environ_disallowed() -> None:
    with pytest.raises(UndefinedError):
        try:
            os.environ["TEST_ENV"] = "test_value"
            assert DslEvaluator({}).eval("{{ os.environ['TEST_ENV'] }}") == "test_value"
        finally:
            del os.environ["TEST_ENV"]

    try:
        os.environ["TEST_ENV"] = "test_value"
        evaluator = evaluator_with_os_environ_as_var()
        assert evaluator.eval("{{ var('TEST_ENV') }}") == "test_value"
    finally:
        del os.environ["TEST_ENV"]
