import inspect
from collections.abc import Callable
from typing import Any

import dagster as dg
import pytest
from dagster._core import decorator_utils
from dagster._core.decorator_utils import (
    get_function_params,
    get_type_hints,
    reflection_cache_scope,
)


class _Resource(dg.ConfigurableResource):
    pass


def _count_signature_calls(monkeypatch: pytest.MonkeyPatch) -> list[Callable[..., Any]]:
    calls: list[Callable[..., Any]] = []
    original = decorator_utils.signature

    def counting_signature(fn: Callable[..., Any]) -> inspect.Signature:
        calls.append(fn)
        return original(fn)

    monkeypatch.setattr(decorator_utils, "signature", counting_signature)
    return calls


def test_no_caching_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _count_signature_calls(monkeypatch)

    def fn(a: int) -> None: ...

    get_function_params(fn)
    get_function_params(fn)
    assert len(calls) == 2


def test_caching_inside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _count_signature_calls(monkeypatch)

    def fn(a: int) -> None: ...

    def other(b: str) -> None: ...

    with reflection_cache_scope():
        first = get_function_params(fn)
        assert get_function_params(fn) is first
        with reflection_cache_scope():  # nested scopes share the outer cache
            assert get_function_params(fn) is first
        assert [p.name for p in get_function_params(other)] == ["b"]
        assert get_type_hints(fn) is get_type_hints(fn)
    assert len(calls) == 2


def test_scope_resets_on_error() -> None:
    with pytest.raises(ValueError):
        with reflection_cache_scope():
            raise ValueError()
    assert decorator_utils._reflection_cache.get() is None  # noqa: SLF001


def test_asset_build_reflects_each_callable_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _count_signature_calls(monkeypatch)

    @dg.asset
    def my_asset(context: dg.AssetExecutionContext, resource: _Resource) -> int:
        return 1

    @dg.asset_check(asset=my_asset)
    def my_check(resource: _Resource) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    assert my_asset.op.required_resource_keys == {"resource"}
    assert my_check.node_def.required_resource_keys == {"resource"}
    assert calls.count(my_asset.op.compute_fn.decorated_fn) == 1  # ty: ignore[unresolved-attribute]
    assert calls.count(my_check.node_def.compute_fn.decorated_fn) == 1  # ty: ignore[unresolved-attribute]


def test_annotation_changes_between_builds_are_observed() -> None:
    def compute(value) -> None: ...

    compute.__annotations__["value"] = int
    first = dg.op(compute)
    assert first.input_defs[0].dagster_type.display_name == "Int"

    compute.__annotations__["value"] = str
    second = dg.op(name="second", ins={})(compute)
    assert second.input_defs[0].dagster_type.display_name == "String"


def test_cache_does_not_outlive_build() -> None:
    def compute(value: Any = None) -> None: ...

    dg.op(compute)
    # The cache, and the strong references it holds, is discarded when the build finishes.
    assert decorator_utils._reflection_cache.get() is None  # noqa: SLF001
