import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Mapping

import pytest
import yaml
from dagster import AssetKey
from dagster._utils.env import environ
from dagster_components.core.component_decl_builder import DefsFileModel
from dagster_components.core.component_defs_builder import (
    YamlComponentDecl,
    build_components_from_component_folder,
)
from dagster_components.impls.sling_replication import SlingReplicationComponent

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

STUB_LOCATION_PATH = Path(__file__).parent / "stub_code_locations" / "sling_location"
COMPONENT_RELPATH = "components/ingest"


def _update_yaml(path: Path, fn) -> None:
    # applies some arbitrary fn to an existing yaml dictionary
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    with open(path, "w") as f:
        yaml.dump(fn(data), f)


@contextmanager
@pytest.fixture(scope="module")
def sling_path() -> Generator[Path, None, None]:
    """Sets up a temporary directory with a replication.yaml and defs.yml file that reference
    the proper temp path.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"HOME": temp_dir}):
            shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)

            # update the replication yaml to reference a CSV file in the tempdir
            replication_path = Path(temp_dir) / COMPONENT_RELPATH / "replication.yaml"

            def _update_replication(data: Dict[str, Any]) -> Mapping[str, Any]:
                placeholder_data = data["streams"].pop("<PLACEHOLDER>")
                data["streams"][f"file://{temp_dir}/input.csv"] = placeholder_data
                return data

            _update_yaml(replication_path, _update_replication)

            # update the defs yaml to add a duckdb instance
            defs_path = Path(temp_dir) / COMPONENT_RELPATH / "defs.yml"

            def _update_defs(data: Dict[str, Any]) -> Mapping[str, Any]:
                data["component_params"]["connections"][0]["instance"] = f"{temp_dir}/duckdb"
                return data

            _update_yaml(defs_path, _update_defs)

            yield Path(temp_dir)


def test_python_params(sling_path: Path) -> None:
    component = SlingReplicationComponent.from_decl_node(
        context=script_load_context(),
        decl_node=YamlComponentDecl(
            path=sling_path / COMPONENT_RELPATH,
            defs_file_model=DefsFileModel(
                component_type="sling_replication",
                component_params={},
            ),
        ),
    )
    assert get_asset_keys(component) == {
        AssetKey("input_csv"),
        AssetKey("input_duckdb"),
    }


def test_load_from_path(sling_path: Path) -> None:
    components = build_components_from_component_folder(
        script_load_context(), sling_path / "components"
    )
    assert len(components) == 1
    assert get_asset_keys(components[0]) == {
        AssetKey("input_csv"),
        AssetKey("input_duckdb"),
    }

    assert_assets(components[0], 2)
