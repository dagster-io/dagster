import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Optional

import dagster as dg
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import instance_for_test
from dagster.components.testing import create_defs_folder_sandbox
from dagster.components.testing.test_cases import TestTranslation
from dagster_omni import OmniComponent

from dagster_omni_tests.utils import create_sample_document, create_sample_workspace_data


def _write_sample_state(instance: dg.DagsterInstance) -> None:
    workspace_data = create_sample_workspace_data([create_sample_document()])
    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "state.json"
        state_path.write_text(dg.serialize_value(workspace_data))
        assert instance.defs_state_storage is not None
        instance.defs_state_storage.upload_state_from_path(
            path=state_path, version="123", key=OmniComponent.__name__
        )


@contextmanager
def setup_omni_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[OmniComponent, Definitions]]:
    """Sets up a components project with an omni component based on provided params."""
    with create_defs_folder_sandbox() as sandbox, instance_for_test() as instance:
        _write_sample_state(instance)
        defs_path = sandbox.scaffold_component(
            component_cls=OmniComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, OmniComponent)
            yield component, defs


class TestOmniTranslation(TestTranslation):
    def test_translation(
        self,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[dg.AssetKey], dg.AssetKey]],
    ) -> None:
        body = {
            "type": "dagster_omni.OmniComponent",
            "attributes": {
                "workspace": {
                    "base_url": "https://test.omniapp.co",
                    "api_key": "test-key",
                },
            },
        }
        body["attributes"]["translation"] = attributes
        with setup_omni_component(defs_yaml_contents=body) as (_, defs):
            specs = [
                spec
                for spec in defs.get_all_asset_specs()
                if "dagster/auto_created_stub_asset" not in spec.metadata
            ]
            assert len(specs) == 1
            spec = specs[0]

            expected_key = dg.AssetKey(["analytics", "reports", "User Analysis"])
            if key_modifier:
                expected_key = key_modifier(expected_key)

            assert assertion(spec)
            assert spec.key == expected_key


def test_per_object_type_translation() -> None:
    body = {
        "type": "dagster_omni.OmniComponent",
        "attributes": {
            "workspace": {
                "base_url": "https://test.omniapp.co",
                "api_key": "test-key",
            },
            "translation": {
                "metadata": {"foo_global": "bar_global", "foo_document": "OVERRIDE_ME"},
                "for_document": {
                    "key_prefix": "document_prefix",
                    "metadata": {"foo": "bar", "foo_document": "bar_document"},
                },
                "for_query": {"key_prefix": "query_prefix"},
            },
        },
    }
    with setup_omni_component(defs_yaml_contents=body) as (_, defs):
        specs = [
            spec
            for spec in defs.get_all_asset_specs()
            if "dagster/auto_created_stub_asset" not in spec.metadata
        ]
        assert len(specs) == 1
        spec = specs[0]

        assert spec.key == dg.AssetKey(["document_prefix", "analytics", "reports", "User Analysis"])
        assert spec.metadata["foo_global"] == "bar_global"
        assert spec.metadata["foo_document"] == "bar_document"
        assert spec.deps == [dg.AssetDep(dg.AssetKey(["query_prefix", "users"]))]
