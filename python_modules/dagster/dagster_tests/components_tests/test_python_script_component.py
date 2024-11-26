from pathlib import Path

from dagster._components import ComponentCollection, ComponentLoadContext
from dagster._components.impls.python_script_component import PythonScript
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.pipes.subprocess import PipesSubprocessClient

LOCATION_PATH = Path(__file__).parent / "code_locations" / "python_script_location"


def test_individual() -> None:
    component = PythonScript(LOCATION_PATH / "scripts" / "script_one.py")
    defs = component.build_defs(ComponentLoadContext({"pipes_client": PipesSubprocessClient()}))

    assert len(defs.get_asset_graph().get_all_asset_keys()) == 1
    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success


def test_individual_spec_override() -> None:
    component = PythonScript(
        path=LOCATION_PATH / "scripts" / "script_one.py",
        specs=[AssetSpec("a"), AssetSpec("b", deps=["up1", "up2"])],
    )
    defs = component.build_defs(ComponentLoadContext({"pipes_client": PipesSubprocessClient()}))

    assert len(defs.get_asset_graph().get_all_asset_keys()) == 4
    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success


def test_collection() -> None:
    component = ComponentCollection(
        PythonScript, [PythonScript(path) for path in (LOCATION_PATH / "scripts").rglob("*.py")]
    )
    defs = component.build_defs(ComponentLoadContext({"pipes_client": PipesSubprocessClient()}))

    assert len(defs.get_asset_graph().get_all_asset_keys()) == 3
    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success
