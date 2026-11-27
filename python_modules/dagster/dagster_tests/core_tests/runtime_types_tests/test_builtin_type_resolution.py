from typing import Any

import dagster as dg
import pytest
from dagster._check import CheckError
from dagster._config.config_type import ConfigType
from dagster._core.types import dagster_type
from dagster._core.types.dagster_type import DagsterType, resolve_dagster_type
from dagster._utils import typing_api

_LIST_INT = dg.List[int]


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (None, dg.Any),
        (Any, dg.Any),
        (int, dg.Int),
        (float, dg.Float),
        (bool, dg.Bool),
        (str, dg.String),
        (type(None), dg.Nothing),
        (_LIST_INT, _LIST_INT),
    ],
)
def test_builtin_resolution_skips_typing_introspection(
    annotation: object, expected: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = resolve_dagster_type(expected)

    def unexpected_introspection(_: object) -> bool:
        pytest.fail("Known builtin and already-resolved types need no typing introspection")

    monkeypatch.setattr(typing_api, "is_typing_type", unexpected_introspection)
    assert resolve_dagster_type(annotation) is resolved


@pytest.mark.parametrize("annotation", [ConfigType, DagsterType])
def test_type_classes_still_rejected(annotation: object) -> None:
    with pytest.raises(CheckError):
        resolve_dagster_type(annotation)


def test_scalar_subclass_does_not_resolve_as_builtin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dagster_type, "_PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY", {})

    class CustomInt(int):
        pass

    custom = dg.DagsterType(
        type_check_fn=lambda _, value: isinstance(value, CustomInt), name="Custom"
    )
    dg.make_python_type_usable_as_dagster_type(CustomInt, custom)
    assert resolve_dagster_type(CustomInt) is custom
    assert resolve_dagster_type(int) is resolve_dagster_type(dg.Int)
