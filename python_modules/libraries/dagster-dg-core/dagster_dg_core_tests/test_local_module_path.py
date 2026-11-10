import re
import textwrap
from pathlib import Path

import pytest
from dagster_dg_core.context import DgContext
from dagster_dg_core.error import DgError


def _make_project(root: Path, *, package_under_src: bool, unrelated_src: bool) -> None:
    (root / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = "foo-bar"
            version = "0.0.1"

            [tool.dg]
            directory_type = "project"

            [tool.dg.project]
            root_module = "foo_bar"
        """)
    )
    package_root = root / "src" if package_under_src else root
    (package_root / "foo_bar" / "defs").mkdir(parents=True)
    (package_root / "foo_bar" / "__init__.py").write_text("")
    (package_root / "foo_bar" / "defs" / "__init__.py").write_text("")
    (package_root / "foo_bar" / "definitions.py").write_text("")
    if unrelated_src:
        # A top-level `src/` that does not hold the project package, e.g. a legacy directory
        # in a monorepo whose packages live at the root.
        (root / "src" / "legacy").mkdir(parents=True)


def _context(root: Path) -> DgContext:
    return DgContext.from_file_discovery_and_command_line_config(root, {})


@pytest.mark.parametrize(
    ("package_under_src", "unrelated_src"),
    [(True, False), (False, False), (False, True)],
    ids=["src-layout", "flat-layout", "flat-layout-with-unrelated-src-dir"],
)
def test_get_path_for_local_module(tmp_path: Path, package_under_src: bool, unrelated_src: bool):
    _make_project(tmp_path, package_under_src=package_under_src, unrelated_src=unrelated_src)
    package_root = tmp_path / "src" if package_under_src else tmp_path
    context = _context(tmp_path)

    assert context.get_path_for_local_module("foo_bar.defs") == package_root / "foo_bar" / "defs"
    assert (
        context.get_path_for_local_module("foo_bar.definitions")
        == package_root / "foo_bar" / "definitions.py"
    )


def test_get_path_for_local_module_missing(tmp_path: Path):
    _make_project(tmp_path, package_under_src=False, unrelated_src=True)
    context = _context(tmp_path)

    with pytest.raises(DgError, match=re.escape("Cannot find module `foo_bar.missing`")):
        context.get_path_for_local_module("foo_bar.missing")


@pytest.mark.parametrize(
    ("package_under_src", "unrelated_src"),
    [(True, False), (False, False), (False, True)],
    ids=["src-layout", "flat-layout", "flat-layout-with-unrelated-src-dir"],
)
def test_get_path_for_new_local_module(
    tmp_path: Path, package_under_src: bool, unrelated_src: bool
):
    _make_project(tmp_path, package_under_src=package_under_src, unrelated_src=unrelated_src)
    package_root = tmp_path / "src" if package_under_src else tmp_path
    context = _context(tmp_path)

    assert (
        context.get_path_for_local_module("foo_bar.defs.new", require_exists=False)
        == package_root / "foo_bar" / "defs" / "new"
    )
