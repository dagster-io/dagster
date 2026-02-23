"""Tests for cross-folder resource sharing with post-processing.

Regression tests for https://github.com/dagster-io/dagster/issues/32925

When a subfolder has a defs.yaml with post-processing, assets in that subfolder
should still be able to access resources defined in a parent folder's resources.py.
Previously, the post-processing would trigger premature repository resolution
(via resolve_asset_graph() -> get_repository_def()), which validated resource
requirements before parent resources were merged into the Definitions.
"""

import importlib
import random
import textwrap
from pathlib import Path

import dagster as dg
from dagster._utils import alter_sys_path
from dagster.components.core.component_tree import ComponentTree
from dagster.components.utils import ensure_loadable_path


def _create_cross_folder_resource_project(
    tmp_path: Path,
    *,
    post_processing_target: str = "*",
    use_tagged_assets: bool = False,
) -> tuple[Path, str]:
    """Creates a minimal project with:
    - A parent-level resources.py defining a shared resource
    - A subfolder with defs.yaml using post-processing and assets that
      depend on the shared resource
    """
    project_name = f"test_proj_{random.randint(0, 2**32 - 1)}"
    project_root = tmp_path / project_name
    project_root.mkdir()

    # pyproject.toml
    (project_root / "pyproject.toml").write_text(
        textwrap.dedent(f"""
        [build-system]
        requires = ["setuptools", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{project_name}"
        version = "0.1.0"
        dependencies = ["dagster"]

        [tool.dg]
        directory_type = "project"

        [tool.dg.project]
        root_module = "{project_name}"
        code_location_name = "{project_name}"
        """)
    )

    # Python package
    pkg_dir = project_root / project_name
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").touch()

    # defs directory
    defs_dir = pkg_dir / "defs"
    defs_dir.mkdir()
    (defs_dir / "__init__.py").touch()

    # Shared resources at parent level
    (defs_dir / "resources.py").write_text(
        textwrap.dedent("""
        import dagster as dg

        defs = dg.Definitions(
            resources={"shared_resource": dg.ResourceDefinition.hardcoded_resource("shared_value")}
        )
        """).strip()
    )

    # Subfolder
    sub_dir = defs_dir / "subfolder"
    sub_dir.mkdir()

    # defs.yaml with post-processing in subfolder
    post_processing_yaml = textwrap.dedent(f"""
    type: dagster.DefsFolderComponent

    post_processing:
      assets:
        - target: "{post_processing_target}"
          attributes:
            group_name: "test_group"
    """).strip()
    (sub_dir / "defs.yaml").write_text(post_processing_yaml)

    # Assets in subfolder that depend on shared resource
    if use_tagged_assets:
        (sub_dir / "assets.py").write_text(
            textwrap.dedent("""
            import dagster as dg

            @dg.asset(required_resource_keys={"shared_resource"}, tags={"needs_group": "true"})
            def my_tagged_asset(context) -> None:
                pass

            @dg.asset(required_resource_keys={"shared_resource"})
            def my_untagged_asset(context) -> None:
                pass
            """).strip()
        )
    else:
        (sub_dir / "assets.py").write_text(
            textwrap.dedent("""
            import dagster as dg

            @dg.asset(required_resource_keys={"shared_resource"})
            def my_asset(context) -> None:
                pass
            """).strip()
        )

    return project_root, project_name


def test_cross_folder_resources_with_wildcard_post_processing(tmp_path: Path) -> None:
    """Test that resources defined at a parent level are accessible by subfolder
    assets when the subfolder uses post-processing with target='*'.

    This is the exact scenario reported in issue #32925.
    """
    project_root, project_name = _create_cross_folder_resource_project(
        tmp_path, post_processing_target="*"
    )

    with (
        alter_sys_path(to_add=[str(project_root)], to_remove=[]),
        ensure_loadable_path(project_root),
    ):
        module = importlib.import_module(f"{project_name}.defs")
        tree = ComponentTree.from_module(
            defs_module=module, project_root=project_root
        )

        # Build defs - this should NOT raise DagsterInvalidDefinitionError
        defs = tree.build_defs()

        # Verify the asset was discovered
        specs = {spec.key: spec for spec in defs.resolve_all_asset_specs()}
        assert dg.AssetKey("my_asset") in specs

        # Verify post-processing was applied (group_name should be "test_group")
        assert specs[dg.AssetKey("my_asset")].group_name == "test_group"

        # Verify the shared resource is available
        assert "shared_resource" in (defs.resources or {})

        # Full validation should pass - all resource requirements satisfied
        dg.Definitions.validate_loadable(defs)


def test_cross_folder_resources_with_targeted_post_processing(tmp_path: Path) -> None:
    """Test that resources defined at a parent level are accessible by subfolder
    assets when the subfolder uses post-processing with a targeted selection
    (non-wildcard, e.g. 'tag:needs_group=true').
    """
    project_root, project_name = _create_cross_folder_resource_project(
        tmp_path,
        post_processing_target="tag:needs_group=true",
        use_tagged_assets=True,
    )

    with (
        alter_sys_path(to_add=[str(project_root)], to_remove=[]),
        ensure_loadable_path(project_root),
    ):
        module = importlib.import_module(f"{project_name}.defs")
        tree = ComponentTree.from_module(
            defs_module=module, project_root=project_root
        )

        # Build defs - this should NOT raise DagsterInvalidDefinitionError
        defs = tree.build_defs()

        # Verify both assets were discovered
        specs = {spec.key: spec for spec in defs.resolve_all_asset_specs()}
        assert dg.AssetKey("my_tagged_asset") in specs
        assert dg.AssetKey("my_untagged_asset") in specs

        # Verify targeted post-processing was applied correctly
        assert specs[dg.AssetKey("my_tagged_asset")].group_name == "test_group"
        # The untagged asset should keep its default group
        assert specs[dg.AssetKey("my_untagged_asset")].group_name in (None, "default")

        # Verify the shared resource is available
        assert "shared_resource" in (defs.resources or {})

        # Full validation should pass
        dg.Definitions.validate_loadable(defs)
