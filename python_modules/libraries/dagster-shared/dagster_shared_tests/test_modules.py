from dataclasses import dataclass
from pathlib import Path

import pytest
from dagster_shared.seven import resolve_module_pattern
from dagster_shared.utils import find_uv_workspace_root


@pytest.mark.parametrize("matches_exist", [True, False])
def test_resolve_module_pattern_literal(monkeypatch, matches_exist: bool):
    def fake_find_spec(name):
        if name == "foo":
            return _FakeModuleSpec(["/fake/path/foo"])
        elif matches_exist and name == "foo.bar":
            return _FakeModuleSpec()
        return None

    def fake_iter_modules(path: list[str] | None = None):
        if path is None:
            return [
                (None, "foo", False),
            ]
        elif matches_exist and path == ["/fake/path/foo"]:
            return [(None, "bar", False)]
        return []

    monkeypatch.setattr("dagster_shared.seven.importlib.util.find_spec", fake_find_spec)
    monkeypatch.setattr("dagster_shared.seven.pkgutil.iter_modules", fake_iter_modules)

    result = resolve_module_pattern("foo.bar")
    if matches_exist:
        assert result == ["foo.bar"]
    else:
        assert result == []


def test_resolve_module_pattern_top_level_standalone_wildcard(monkeypatch):
    def fake_find_spec(name: str):
        return _FakeModuleSpec()

    def fake_iter_modules(path: list[str] | None = None):
        return [
            (None, "foo", False),
            (None, "bar", False),
            (None, "baz", False),
        ]

    monkeypatch.setattr("dagster_shared.seven.importlib.util.find_spec", fake_find_spec)
    monkeypatch.setattr("dagster_shared.seven.pkgutil.iter_modules", fake_iter_modules)

    monkeypatch.setattr(
        "dagster_shared.seven.importlib.util.find_spec",
        fake_find_spec,
    )

    result = resolve_module_pattern("*")

    assert set(result) == {"foo", "bar", "baz"}


@pytest.mark.parametrize("matches_exist", [True, False])
def test_resolve_module_pattern_embedded_wildcard_start(monkeypatch, matches_exist: bool):
    def fake_find_spec(name):
        if name in ["bar", "baz"]:
            return _FakeModuleSpec([f"/fake/path/{name}"])
        if matches_exist and name in {"bar.foo", "baz.foo"}:
            return _FakeModuleSpec()
        return None

    def fake_iter_modules(path: list[str] | None = None):
        if matches_exist and path == ["/fake/path/bar"]:
            return [(None, "foo", False)]
        elif matches_exist and path == ["/fake/path/bar"]:
            return [(None, "foo", False)]
        return [
            (None, "bar", False),
            (None, "baz", False),
        ]

    monkeypatch.setattr("dagster_shared.seven.importlib.util.find_spec", fake_find_spec)
    monkeypatch.setattr("dagster_shared.seven.pkgutil.iter_modules", fake_iter_modules)

    result = resolve_module_pattern("*.foo")
    if matches_exist:
        assert result == ["bar.foo", "baz.foo"]
    else:
        assert result == []


@pytest.mark.parametrize("matches_exist", [True, False])
def test_resolve_wildcard_modules_embedded_wildcard_middle(monkeypatch, matches_exist: bool):
    def fake_find_spec(name: str) -> _FakeModuleSpec | None:
        if name == "foo":
            return _FakeModuleSpec(["/fake/path/foo"])
        if matches_exist and name in ["foo.bar.models", "foo.baz.models"]:
            return _FakeModuleSpec()
        return None

    def fake_iter_modules(path: list[str] | None = None):
        if path == ["/fake/path/foo"]:
            return [
                (None, "bar", False),
                (None, "baz", False),
            ]
        return []

    monkeypatch.setattr("dagster_shared.seven.importlib.util.find_spec", fake_find_spec)
    monkeypatch.setattr("dagster_shared.seven.pkgutil.iter_modules", fake_iter_modules)

    result = resolve_module_pattern("foo.*.models")
    if matches_exist:
        assert result == ["foo.bar.models", "foo.baz.models"]
    else:
        assert result == []


@pytest.mark.parametrize("matches_exist", [True, False])
def test_resolve_module_pattern_embedded_wildcard_end(monkeypatch, matches_exist: bool):
    def fake_find_spec(name):
        if name == "foo":
            return _FakeModuleSpec(["/fake/path/foo"])
        if matches_exist and name in {"foo.bar", "foo.baz"}:
            return _FakeModuleSpec()
        return None

    def fake_iter_modules(path: list[str] | None = None):
        if path == ["/fake/path/foo"]:
            return [
                (None, "bar", False),
                (None, "baz", False),
            ]
        return []

    monkeypatch.setattr("dagster_shared.seven.importlib.util.find_spec", fake_find_spec)
    monkeypatch.setattr("dagster_shared.seven.pkgutil.iter_modules", fake_iter_modules)

    result = resolve_module_pattern("foo.*")
    if matches_exist:
        assert result == ["foo.bar", "foo.baz"]
    else:
        assert result == []


@dataclass
class _FakeModuleSpec:
    submodule_search_locations: list[str] | None = None


def test_find_uv_workspace_root_accepts_empty_workspace_section(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[tool.uv.workspace]\n", encoding="utf-8")
    child = tmp_path / "project"
    child.mkdir()
    assert find_uv_workspace_root(child) == (tmp_path, {})


def test_find_uv_workspace_root_does_not_accept_plain_uv_config(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[tool.uv]\nmanaged = false\n", encoding="utf-8")
    assert find_uv_workspace_root(tmp_path) is None
