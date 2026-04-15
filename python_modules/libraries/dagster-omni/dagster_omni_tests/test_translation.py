from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import dagster as dg
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster.components.testing.test_cases import TestTranslation
from dagster_omni import OmniComponent

from dagster_omni_tests.utils import create_sample_document, create_sample_workspace_data


def _mock_write_state_to_path(self, state_path):
    workspace_data = create_sample_workspace_data([create_sample_document()])
    state_path.write_text(dg.serialize_value(workspace_data))


@contextmanager
def setup_omni_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[OmniComponent, Definitions]]:
    """Sets up a components project with an omni component based on provided params."""
    with (
        create_defs_folder_sandbox() as sandbox,
        environ({"DAGSTER_IS_DEV_CLI": "1"}),
        patch.object(OmniComponent, "write_state_to_path", _mock_write_state_to_path),
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=OmniComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                component,
                defs,
            ),
        ):
            assert isinstance(component, OmniComponent)
            yield component, defs


class TestOmniTranslation(TestTranslation):
    def test_translation(
        self,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Callable[[dg.AssetKey], dg.AssetKey] | None,
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
            expected_key = dg.AssetKey(["analytics", "reports", "User Analysis"])
            if key_modifier:
                expected_key = key_modifier(expected_key)

            spec = defs.get_assets_def(expected_key).get_asset_spec(expected_key)
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
        key = dg.AssetKey(["document_prefix", "analytics", "reports", "User Analysis"])
        spec = defs.get_assets_def(key).get_asset_spec(key)
        assert spec.key == key
        assert spec.metadata["foo_global"] == "bar_global"
        assert spec.metadata["foo_document"] == "bar_document"
        assert spec.deps == [dg.AssetDep(dg.AssetKey(["query_prefix", "users"]))]
