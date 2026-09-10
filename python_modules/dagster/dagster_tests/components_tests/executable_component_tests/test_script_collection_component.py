import dagster as dg
import pytest
from dagster.components.lib.script_collection_component.script_collection_component import (
    ScriptCollectionComponent,
)
from dagster.components.testing import copy_code_to_file, create_defs_folder_sandbox

COMPONENT_TYPE = "dagster.components.lib.script_collection_component.script_collection_component.ScriptCollectionComponent"


def test_script_discovery_and_asset_keys() -> None:
    """Scripts are discovered and asset keys are derived from paths."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ScriptCollectionComponent,
            defs_yaml_contents={"type": COMPONENT_TYPE},
        )

        (defs_path / "top_level.py").write_text("print('top')")
        subdir = defs_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.py").write_text("print('nested')")

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_, defs):
            specs = defs.get_all_asset_specs()
            keys = {spec.key for spec in specs}
            assert keys == {
                dg.AssetKey(["top_level"]),
                dg.AssetKey(["subdir", "nested"]),
            }


@pytest.mark.parametrize(
    "include,exclude,files,expected_keys",
    [
        # Defaults
        (["*"], [], {"a.py": "", "b.py": ""}, [["a"], ["b"]]),
        # Basic include pattern
        (["*.py"], [], {"a.py": "", "b.txt": ""}, [["a"]]),
        # Exclude overrides include
        (["*.py"], ["utils.py"], {"main.py": "", "utils.py": ""}, [["main"]]),
        # Subdirectory glob
        (["scripts/**/*.py"], [], {"scripts/a.py": "", "outside.py": ""}, [["scripts", "a"]]),
        # No matches
        (["*.nonexistent"], [], {"a.py": ""}, []),
    ],
    ids=["defaults", "include-only", "with-exclude", "subdir-glob", "no-matches"],
)
def test_include_exclude_patterns(include, exclude, files, expected_keys) -> None:
    """Include/exclude patterns filter scripts correctly."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ScriptCollectionComponent,
            defs_yaml_contents={
                "type": COMPONENT_TYPE,
                "attributes": {"include": include, "exclude": exclude},
            },
        )

        for path, content in files.items():
            file_path = defs_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_, defs):
            specs = defs.get_all_asset_specs()
            assert {spec.key for spec in specs} == {dg.AssetKey(k) for k in expected_keys}


def test_script_with_dagster_config_block() -> None:
    """Script with # /// dagster YAML block has custom config applied."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ScriptCollectionComponent,
            defs_yaml_contents={
                "type": COMPONENT_TYPE,
                "attributes": {"include": ["*.py"]},
            },
        )

        script_content = """\
# /// dagster
# specs:
#   - key: "my/custom_key"
#     description: "My custom asset"
#     group_name: my_group
# ///
print('hello')
"""
        (defs_path / "my_script.py").write_text(script_content)

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_, defs):
            spec = defs.get_all_asset_specs()[0]
            assert spec.key == dg.AssetKey(["my", "custom_key"])
            assert spec.description == "My custom asset"
            assert spec.group_name == "my_group"


def test_script_execution_with_pipes() -> None:
    """Script executes and pipes metadata is captured."""

    def code_to_copy():
        from dagster_pipes import open_dagster_pipes

        if __name__ == "__main__":
            with open_dagster_pipes() as context:
                context.report_asset_materialization(metadata={"result": "success"})

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ScriptCollectionComponent,
            defs_yaml_contents={"type": COMPONENT_TYPE},
        )

        copy_code_to_file(code_to_copy, defs_path / "script.py")

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_, defs):
            result = dg.materialize([defs.get_assets_def("script")])
            assert result.success
            mats = result.get_asset_materialization_events()
            assert mats[0].step_materialization_data.materialization.metadata == {
                "result": dg.TextMetadataValue("success")
            }
