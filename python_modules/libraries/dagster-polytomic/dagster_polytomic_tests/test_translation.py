import tempfile
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

import dagster as dg
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import instance_for_test
from dagster.components.testing import create_defs_folder_sandbox
from dagster.components.testing.test_cases import TestTranslation
from dagster_polytomic import PolytomicComponent

from dagster_polytomic_tests.utils import (
    create_sample_bulk_sync,
    create_sample_bulk_sync_schema,
    create_sample_connection,
    create_sample_workspace_data,
)


def _write_sample_state(instance: dg.DagsterInstance) -> None:
    # Create connections
    source_conn = create_sample_connection("conn-source", "PostgreSQL Source", "postgres")
    dest_conn = create_sample_connection("conn-dest", "Snowflake Dest", "snowflake")

    # Create bulk sync with destination configuration
    bulk_sync = create_sample_bulk_sync(
        bulk_sync_id="sync-1",
        name="Test Sync",
        source_connection_id="conn-source",
        destination_connection_id="conn-dest",
        destination_configuration_schema="public",
    )

    # Create schemas
    schema1 = create_sample_bulk_sync_schema("schema-1", output_name="users")

    # Create workspace data
    workspace_data = create_sample_workspace_data(
        connections=[source_conn, dest_conn],
        bulk_syncs=[bulk_sync],
        schemas_by_bulk_sync_id={"sync-1": [schema1]},
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "state.json"
        state_path.write_text(dg.serialize_value(workspace_data))
        assert instance.defs_state_storage is not None
        instance.defs_state_storage.upload_state_from_path(
            path=state_path, version="123", key=PolytomicComponent.__name__
        )


@contextmanager
def setup_polytomic_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[PolytomicComponent, Definitions]]:
    """Sets up a components project with a polytomic component based on provided params."""
    with create_defs_folder_sandbox() as sandbox, instance_for_test() as instance:
        _write_sample_state(instance)
        defs_path = sandbox.scaffold_component(
            component_cls=PolytomicComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, PolytomicComponent)
            yield component, defs


class TestPolytomicTranslation(TestTranslation):
    def test_translation(
        self,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[dg.AssetKey], dg.AssetKey]],
    ) -> None:
        body = {
            "type": "dagster_polytomic.PolytomicComponent",
            "attributes": {
                "workspace": {
                    "api_key": "test-key",
                },
            },
        }
        body["attributes"]["translation"] = attributes
        with setup_polytomic_component(defs_yaml_contents=body) as (_, defs):
            specs = [
                spec
                for spec in defs.get_all_asset_specs()
                if "dagster/auto_created_stub_asset" not in spec.metadata
            ]
            assert len(specs) == 1
            spec = specs[0]

            expected_key = dg.AssetKey(["public", "schema-1"])
            if key_modifier:
                expected_key = key_modifier(expected_key)

            assert assertion(spec)
            assert spec.key == expected_key


def test_per_object_type_translation() -> None:
    body = {
        "type": "dagster_polytomic.PolytomicComponent",
        "attributes": {
            "workspace": {
                "api_key": "test-key",
            },
            "translation": {
                "metadata": {"foo_global": "bar_global", "foo_schema": "OVERRIDE_ME"},
                "for_schema": {
                    "key_prefix": "schema_prefix",
                    "metadata": {"foo": "bar", "foo_schema": "bar_schema"},
                },
            },
        },
    }
    with setup_polytomic_component(defs_yaml_contents=body) as (_, defs):
        specs = [
            spec
            for spec in defs.get_all_asset_specs()
            if "dagster/auto_created_stub_asset" not in spec.metadata
        ]
        assert len(specs) == 1
        spec = specs[0]

        assert spec.key == dg.AssetKey(["schema_prefix", "public", "schema-1"])
        assert spec.metadata["foo_global"] == "bar_global"
        assert spec.metadata["foo_schema"] == "bar_schema"
