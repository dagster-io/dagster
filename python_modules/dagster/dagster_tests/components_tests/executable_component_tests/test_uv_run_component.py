import dagster as dg
from dagster.components.lib.executable_component.script_utils import ScriptSpec
from dagster.components.lib.executable_component.uv_run_component import UvRunComponent
from dagster.components.testing import create_defs_folder_sandbox

SCRIPT_CONTENT = """# /// script
# dependencies = [
#   "dagster_pipes",
#   "pycowsay",
# ]
# ///
import sys

from dagster_pipes import open_dagster_pipes
from pycowsay import main

assert main

if __name__ == "__main__":
    with open_dagster_pipes() as context:
        context.report_asset_materialization(
            metadata={"arg": sys.argv[1], "pycowsay_module_name": sys.modules["pycowsay"].__name__}
        )
"""


def test_pipes_subprocess_script_hello_world() -> None:
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=UvRunComponent,
            defs_yaml_contents={
                "type": "dagster.UvRunComponent",
                "attributes": {
                    "execution": {
                        "name": "op_name",
                        "path": "script.py",
                        "args": ["hello"],
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
        execute_path.write_text(SCRIPT_CONTENT)

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.UvRunComponent)
            assert isinstance(component.execution, ScriptSpec)
            assets_def = defs.get_assets_def("asset")
            result = dg.materialize([assets_def])
            assert result.success
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1
            assert next(iter(mats)).metadata == {
                "arg": dg.TextMetadataValue("hello"),
                "pycowsay_module_name": dg.TextMetadataValue("pycowsay"),
            }
