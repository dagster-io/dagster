import re
import textwrap
from pathlib import Path

import pytest
from dagster_dg_core.context import DgContext
from dagster_dg_core.error import DgError


def _make_project(
    root: Path, root_module: str, package_dir: str, other_dirs: tuple[str, ...] = ()
) -> None:
    """Create a dg project whose `root_module` package lives under `root/package_dir`."""
    (root / "pyproject.toml").write_text(
        textwrap.dedent(f"""
            [project]
            name = "foo-bar"
            version = "0.0.1"

            [tool.dg]
            directory_type = "project"

            [tool.dg.project]
            root_module = "{root_module}"
        """)
    )
    package = root / package_dir / Path(*root_module.split("."))
    (package / "defs").mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "defs" / "__init__.py").write_text("")
    (package / "definitions.py").write_text("")
    for other in other_dirs:
        (root / other).mkdir(parents=True)


def _context(root: Path) -> DgContext:
    return DgContext.from_file_discovery_and_command_line_config(root, {})


LAYOUTS = [
    pytest.param("foo_bar", "src", (), id="src-layout"),
    pytest.param("foo_bar", ".", (), id="flat-layout"),
    # A monorepo whose packages live at the root and that keeps an unrelated `src/`.
    pytest.param("foo_bar", ".", ("src/legacy",), id="flat-layout-with-unrelated-src"),
    # An unrelated package under `src/` shares the root module's top-level namespace.
    pytest.param("acme.blue", ".", ("src/acme/other",), id="flat-dotted-root-with-src-namespace"),
    # The root module exists in both places: `src/` keeps precedence, as before.
    pytest.param("foo_bar", "src", ("foo_bar",), id="both-places-prefers-src"),
]


@pytest.mark.parametrize(("root_module", "package_dir", "other_dirs"), LAYOUTS)
def test_get_path_for_local_module(
    tmp_path: Path, root_module: str, package_dir: str, other_dirs: tuple[str, ...]
):
    _make_project(tmp_path, root_module, package_dir, other_dirs)
    package = tmp_path / package_dir / Path(*root_module.split("."))
    context = _context(tmp_path)

    assert context.get_path_for_local_module(root_module) == package
    assert context.get_path_for_local_module(f"{root_module}.defs") == package / "defs"
    assert (
        context.get_path_for_local_module(f"{root_module}.definitions")
        == package / "definitions.py"
    )
    # Paths for modules that do not exist yet (used when scaffolding) land next to the package.
    assert (
        context.get_path_for_local_module(f"{root_module}.defs.new", require_exists=False)
        == package / "defs" / "new"
    )


def test_get_path_for_local_module_missing(tmp_path: Path):
    _make_project(tmp_path, "foo_bar", ".", ("src/legacy",))
    context = _context(tmp_path)

    with pytest.raises(DgError, match=re.escape("Cannot find module `foo_bar.missing`")):
        context.get_path_for_local_module("foo_bar.missing")
