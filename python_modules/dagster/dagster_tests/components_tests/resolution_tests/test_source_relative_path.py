import os
from pathlib import Path

from dagster.components.resolved.context import ResolutionContext
from dagster_shared.yaml_utils.source_position import LineCol, SourcePosition, SourcePositionTree


def _context_for(yaml_file: Path) -> ResolutionContext:
    tree = SourcePositionTree(
        position=SourcePosition(
            filename=str(yaml_file),
            start=LineCol(1, 0),
            end=LineCol(1, 0),
        ),
        children={},
    )
    return ResolutionContext.default().with_source_position_tree(tree)


def test_absolute_path_with_parent_segments_is_normalized(tmp_path: Path) -> None:
    # Regression for https://github.com/dagster-io/dagster/issues/33808 — a path like
    # `{{ context.project_root }}/../sibling` renders to an absolute path containing `..`
    # and must be canonicalized so downstream consumers (e.g. DbtProject) see a clean path.
    parent = tmp_path / "parent"
    dagster_project = parent / "dagster_project"
    sibling = parent / "sibling"
    sibling.mkdir(parents=True)
    dagster_project.mkdir()
    yaml_file = dagster_project / "defs.yaml"
    yaml_file.touch()

    ctx = _context_for(yaml_file)
    raw = str(dagster_project / ".." / "sibling")

    resolved = ctx.resolve_source_relative_path(raw)

    assert ".." not in resolved.parts
    assert resolved == Path(os.path.normpath(raw))


def test_absolute_path_with_parent_segments_normalized_when_target_does_not_exist(
    tmp_path: Path,
) -> None:
    # Mirrors the production scenario from #33808: dbt-prepare has not yet created the
    # target directory at config-resolution time, so the helper must normalize without
    # touching the filesystem.
    parent = tmp_path / "parent"
    dagster_project = parent / "dagster_project"
    dagster_project.mkdir(parents=True)
    yaml_file = dagster_project / "defs.yaml"
    yaml_file.touch()

    ctx = _context_for(yaml_file)
    nonexistent = parent / "not_yet_created"
    raw = str(dagster_project / ".." / "not_yet_created")
    assert not nonexistent.exists()

    resolved = ctx.resolve_source_relative_path(raw)

    assert ".." not in resolved.parts
    assert resolved == Path(os.path.normpath(raw))


def test_canonical_absolute_path_is_unchanged(tmp_path: Path) -> None:
    target = tmp_path / "abc"
    target.mkdir()
    yaml_file = tmp_path / "defs.yaml"
    yaml_file.touch()

    ctx = _context_for(yaml_file)

    # normpath of an already-canonical path returns it unchanged on every platform,
    # without resolving symlinks (e.g. macOS /var -> /private/var).
    assert ctx.resolve_source_relative_path(str(target)) == Path(os.path.normpath(str(target)))


def test_absolute_path_branch_does_not_resolve_symlinks(tmp_path: Path) -> None:
    # Sean Mackesey's review concern: `Path.resolve()` follows symlinks, which would silently
    # change paths in symlinked Buildkite/Docker layouts and on macOS where /var -> /private/var.
    # The helper must use normpath semantics, not resolve semantics.
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link_dir = tmp_path / "link"
    try:
        link_dir.symlink_to(real_dir, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Windows without developer mode can't create symlinks; skip the assertion in that case.
        return

    yaml_file = tmp_path / "defs.yaml"
    yaml_file.touch()
    ctx = _context_for(yaml_file)

    resolved = ctx.resolve_source_relative_path(str(link_dir))

    # The symlink path is preserved — we did not silently rewrite to the target.
    assert resolved == link_dir


def test_relative_path_resolved_against_source_dir(tmp_path: Path) -> None:
    source_dir = tmp_path / "src"
    target = tmp_path / "target"
    source_dir.mkdir()
    target.mkdir()
    yaml_file = source_dir / "defs.yaml"
    yaml_file.touch()

    ctx = _context_for(yaml_file)

    # The relative branch still calls .resolve() (preserving prior behavior); compare
    # against the same operation so the test is robust on platforms where tmp_path
    # itself contains symlinks.
    assert ctx.resolve_source_relative_path("../target") == target.resolve()


def test_relative_path_without_source_position_tree_is_unchanged() -> None:
    ctx = ResolutionContext.default()

    resolved = ctx.resolve_source_relative_path("relative/path")

    assert resolved == Path("relative/path")
    assert not resolved.is_absolute()
