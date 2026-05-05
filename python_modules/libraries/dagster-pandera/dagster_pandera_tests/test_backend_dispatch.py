"""Backend dispatch logic for ``_resolve_typing_type``.

Verifies the module-path parser and fallback behaviour. End-to-end
backend coverage (pandas, polars) lives in test_dagster_pandera.py and
test_polars.py respectively.
"""

import sys

import pandas as pd
import pytest
from dagster_pandera import _BACKEND_DF_TYPE, _resolve_typing_type

# ########################
# ##### HELPERS
# ########################


def _fake_schema(backend: str) -> object:
    cls = type("FakeSchema", (), {})
    cls.__module__ = f"pandera.api.{backend}.container"
    return cls()


# ########################
# ##### TESTS
# ########################


@pytest.mark.parametrize("backend", list(_BACKEND_DF_TYPE.keys()))
def test_resolve_typing_type_per_backend(backend: str) -> None:
    import importlib

    mod_name, attr = _BACKEND_DF_TYPE[backend]
    expected = getattr(importlib.import_module(mod_name), attr)

    schema = _fake_schema(backend)
    assert _resolve_typing_type(schema) is expected


def test_resolve_typing_type_unknown_backend_falls_back() -> None:
    schema = _fake_schema("totally_made_up_backend")
    assert _resolve_typing_type(schema) is pd.DataFrame


def test_resolve_typing_type_non_pandera_module_falls_back() -> None:
    cls = type("WeirdSchema", (), {})
    cls.__module__ = "some.other.library"
    assert _resolve_typing_type(cls()) is pd.DataFrame


def test_resolve_typing_type_missing_backend_lib_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "polars", None)
    schema = _fake_schema("polars")
    assert _resolve_typing_type(schema) is pd.DataFrame
