import dagster as dg
from dagster._core.definitions.asset_selection import AssetSelection
from dagster.components.lib.executable_component.python_script_component import (
    PythonScriptComponent,
    ScriptSpec,
)
from dagster.components.testing import copy_code_to_file, create_defs_folder_sandbox


def test_pipes_subprocess_script_hello_world() -> None:
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {
                        "name": "op_name",
                        "path": "script.py",
                    },
                    "assets": [
                        {
                            "key": "asset",
                        }
                    ],
                },
            },
        )
        execute_path = defs_path / "script.py"
        execute_path.write_text("print('hello world')")

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.PythonScriptComponent)
            assert isinstance(component.execution, ScriptSpec)
            assets_def = defs.get_assets_def("asset")
            result = dg.materialize([assets_def])
            assert result.success
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1


def test_pipes_subprocess_script_with_custom_materialize_result() -> None:
    def code_to_copy():
        from dagster_pipes import open_dagster_pipes

        if __name__ == "__main__":
            with open_dagster_pipes() as context:
                context.report_asset_materialization(metadata={"foo": "bar"})

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {
                        "path": "op_name.py",
                    },
                    "assets": [
                        {
                            "key": "asset",
                        }
                    ],
                },
            },
        )
        execute_path = defs_path / "op_name.py"
        copy_code_to_file(code_to_copy, execute_path)

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.PythonScriptComponent)
            assert isinstance(component.execution, ScriptSpec)
            assets_def = defs.get_assets_def("asset")
            result = dg.materialize([assets_def])
            assert result.success
            assert assets_def.op.name == "op_name"
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1
            assert mats[0].metadata == {"foo": dg.TextMetadataValue("bar")}


def test_pipes_subprocess_script_with_name_override() -> None:
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {
                        "name": "op_name_override",
                        "path": "op_name.py",
                    },
                    "assets": [
                        {
                            "key": "asset",
                        }
                    ],
                },
            },
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            _component,
            defs,
        ):
            assert defs.get_assets_def("asset").op.name == "op_name_override"


def test_pipes_subprocess_script_with_checks_only() -> None:
    def code_to_copy():
        from dagster_pipes import open_dagster_pipes

        if __name__ == "__main__":
            with open_dagster_pipes() as context:
                context.report_asset_check(
                    asset_key="asset",
                    check_name="check_name",
                    passed=True,
                )

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {
                        "path": "only_checks.py",
                    },
                    "assets": [],
                    "checks": [
                        {
                            "asset": "asset",
                            "name": "check_name",
                        }
                    ],
                },
            },
        )
        execute_path = defs_path / "only_checks.py"
        copy_code_to_file(code_to_copy, execute_path)

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.PythonScriptComponent)
            assert isinstance(component.execution, ScriptSpec)
            assert defs.asset_checks
            check_def = next(iter(defs.asset_checks))
            result = dg.materialize([check_def], selection=AssetSelection.all_asset_checks())
            assert result.success
            assert check_def.op.name == "only_checks"
            aces = result.get_asset_check_evaluations()
            assert len(aces) == 1
            evaluation = aces[0]
            assert evaluation.passed
            assert evaluation.asset_key == dg.AssetKey("asset")
            assert evaluation.check_name == "check_name"


def test_pipes_subprocess_with_args() -> None:
    def op_name_contents():
        import sys

        from dagster_pipes import open_dagster_pipes

        if __name__ == "__main__":
            with open_dagster_pipes() as context:
                context.report_asset_materialization(metadata={"arg": sys.argv[1]})

    def template_vars_content():
        import dagster as dg

        @dg.template_var
        def arg_list():
            return ["arg_value"]

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {
                        "path": "op_name.py",
                        "args": "{{ arg_list }}",
                    },
                    "assets": [
                        {
                            "key": "asset",
                        }
                    ],
                },
                "template_vars_module": ".template_vars",
            },
        )
        execute_path = defs_path / "op_name.py"
        copy_code_to_file(op_name_contents, execute_path)
        template_vars_path = defs_path / "template_vars.py"
        copy_code_to_file(template_vars_content, template_vars_path)

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.PythonScriptComponent)
            assert isinstance(component.execution, ScriptSpec)
            assert component.execution.args == ["arg_value"]
            assets_def = defs.get_assets_def("asset")
            result = dg.materialize([assets_def])
            assert result.success
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1
            assert mats[0].metadata == {"arg": dg.TextMetadataValue("arg_value")}


def test_pipes_subprocess_with_inline_str() -> None:
    def op_name_contents():
        import sys

        from dagster_pipes import open_dagster_pipes

        if __name__ == "__main__":
            with open_dagster_pipes() as context:
                context.report_asset_materialization(metadata={"arg": sys.argv[1]})

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=PythonScriptComponent,
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {
                        "path": "op_name.py",
                        "args": "arg_value",
                    },
                    "assets": [
                        {
                            "key": "asset",
                        }
                    ],
                },
            },
        )
        execute_path = defs_path / "op_name.py"
        copy_code_to_file(op_name_contents, execute_path)

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.PythonScriptComponent)
            assert isinstance(component.execution, ScriptSpec)
            assert component.execution.args == "arg_value"
            assets_def = defs.get_assets_def("asset")
            result = dg.materialize([assets_def])
            assert result.success
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1
            assert mats[0].metadata == {"arg": dg.TextMetadataValue("arg_value")}
