from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster.components.lib.executable_component.script_utils import ScriptSpec
from dagster.components.lib.executable_component.uv_run_component import UvRunComponent
from dagster.components.testing import scaffold_defs_sandbox

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
    with scaffold_defs_sandbox(component_cls=UvRunComponent) as sandbox:
        execute_path = sandbox.defs_folder_path / "script.py"
        execute_path.write_text(SCRIPT_CONTENT)

        with sandbox.load(
            component_body={
                "type": "dagster.components.UvRunComponent",
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
            }
        ) as (component, defs):
            assert isinstance(component, UvRunComponent)
            assert isinstance(component.execution, ScriptSpec)
            assets_def = defs.get_assets_def("asset")
            result = materialize([assets_def])
            assert result.success
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1
            assert next(iter(mats)).metadata == {
                "arg": TextMetadataValue("hello"),
                "pycowsay_module_name": TextMetadataValue("pycowsay"),
            }
