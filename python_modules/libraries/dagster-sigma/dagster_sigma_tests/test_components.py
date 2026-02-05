import os
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, nullcontext
from typing import Any, Optional

import pytest
import responses
from dagster import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster_shared.utils import environ
from dagster_sigma import SigmaBaseUrl, SigmaComponent


@pytest.fixture(autouse=True)
def _setup(sigma_auth_token: str) -> Iterator:
    """Set up instance and activate responses mock for component tests."""
    responses.start()
    try:
        with instance_for_test():
            yield
    finally:
        responses.stop()
        responses.reset()


@contextmanager
def setup_sigma_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[SigmaComponent, Definitions]]:
    """Sets up a components project with a sigma component based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SigmaComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, SigmaComponent)
            yield component, defs


def test_basic_component_load(sigma_sample_data: Any, sigma_auth_token: str) -> None:
    """Test basic component loading."""
    with (
        environ(
            {
                "SIGMA_BASE_URL": SigmaBaseUrl.AWS_US.value,
                "SIGMA_CLIENT_ID": uuid.uuid4().hex,
                "SIGMA_CLIENT_SECRET": uuid.uuid4().hex,
            }
        ),
        setup_sigma_component(
            defs_yaml_contents={
                "type": "dagster_sigma.SigmaComponent",
                "attributes": {
                    "organization": {
                        "base_url": "{{ env.SIGMA_BASE_URL }}",
                        "client_id": "{{ env.SIGMA_CLIENT_ID }}",
                        "client_secret": "{{ env.SIGMA_CLIENT_SECRET }}",
                    },
                },
            }
        ) as (
            component,
            defs,
        ),
    ):
        # Verify that we have the expected assets
        asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
        assert AssetKey("Sample_Workbook") in asset_keys
        assert AssetKey("Orders_Dataset") in asset_keys
        assert component.organization.base_url == SigmaBaseUrl.AWS_US.value
        assert component.organization.client_id == os.environ["SIGMA_CLIENT_ID"]
        assert component.organization.client_secret == os.environ["SIGMA_CLIENT_SECRET"]


@pytest.mark.parametrize(
    "attributes, assertion, should_error",
    [
        ({"group_name": "group"}, lambda asset_spec: asset_spec.group_name == "group", False),
        (
            {"owners": ["team:analytics"]},
            lambda asset_spec: asset_spec.owners == ["team:analytics"],
            False,
        ),
        ({"tags": {"foo": "bar"}}, lambda asset_spec: asset_spec.tags.get("foo") == "bar", False),
        (
            {"kinds": ["snowflake", "dbt"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds and "dbt" in asset_spec.kinds,
            False,
        ),
        (
            {"tags": {"foo": "bar"}, "kinds": ["snowflake", "dbt"]},
            lambda asset_spec: (
                "snowflake" in asset_spec.kinds
                and "dbt" in asset_spec.kinds
                and asset_spec.tags.get("foo") == "bar"
            ),
            False,
        ),
        ({"code_version": "1"}, lambda asset_spec: asset_spec.code_version == "1", False),
        (
            {"description": "some description"},
            lambda asset_spec: asset_spec.description == "some description",
            False,
        ),
        (
            {"metadata": {"foo": "bar"}},
            lambda asset_spec: asset_spec.metadata.get("foo") == "bar",
            False,
        ),
        (
            {"deps": ["customers"]},
            lambda asset_spec: (
                len(asset_spec.deps) == 1 and asset_spec.deps[0].asset_key == AssetKey("customers")
            ),
            False,
        ),
        (
            {"automation_condition": "{{ automation_condition.eager() }}"},
            lambda asset_spec: asset_spec.automation_condition is not None,
            False,
        ),
        (
            {"key_prefix": "cool_prefix"},
            lambda asset_spec: asset_spec.key.has_prefix(["cool_prefix"]),
            False,
        ),
    ],
    ids=[
        "group_name",
        "owners",
        "tags",
        "kinds",
        "tags-and-kinds",
        "code-version",
        "description",
        "metadata",
        "deps",
        "automation_condition",
        "key_prefix",
    ],
)
def test_translation(
    attributes: Mapping[str, Any],
    assertion: Optional[Callable[[AssetSpec], bool]],
    should_error: bool,
    sigma_sample_data: Any,
    sigma_auth_token: str,
) -> None:
    wrapper = pytest.raises(Exception) if should_error else nullcontext()
    with wrapper:
        body = {
            "type": "dagster_sigma.SigmaComponent",
            "attributes": {
                "organization": {
                    "base_url": SigmaBaseUrl.AWS_US.value,
                    "client_id": uuid.uuid4().hex,
                    "client_secret": uuid.uuid4().hex,
                },
            },
        }
        body["attributes"]["translation"] = attributes
        with (
            setup_sigma_component(
                defs_yaml_contents=body,
            ) as (component, defs),
        ):
            if "key_prefix" in attributes:
                key = AssetKey(["cool_prefix", "Sample_Workbook"])
            elif "key" in attributes:
                # For key transformations, we need to determine the expected key
                key = next(iter(defs.resolve_asset_graph().get_all_asset_keys()))
            else:
                key = AssetKey("Sample_Workbook")

            assets_def = defs.get_assets_def(key)
            if assertion:
                assert assertion(assets_def.get_asset_spec(key))


def test_per_content_type_translation(sigma_sample_data: Any, sigma_auth_token: str) -> None:
    body = {
        "type": "dagster_sigma.SigmaComponent",
        "attributes": {
            "organization": {
                "base_url": SigmaBaseUrl.AWS_US.value,
                "client_id": uuid.uuid4().hex,
                "client_secret": uuid.uuid4().hex,
            },
            "translation": {
                "tags": {"custom_tag": "custom_value"},
                "for_workbook": {
                    "tags": {"is_workbook": "true"},
                },
                "for_dataset": {
                    "tags": {"is_dataset": "true"},
                },
            },
        },
    }
    with (
        setup_sigma_component(
            defs_yaml_contents=body,
        ) as (
            component,
            defs,
        ),
    ):
        workbook_spec = defs.get_assets_def(AssetKey("Sample_Workbook")).get_asset_spec(
            AssetKey("Sample_Workbook")
        )
        assert workbook_spec.tags.get("custom_tag") == "custom_value"
        assert workbook_spec.tags.get("is_workbook") == "true"

        dataset_spec = defs.get_assets_def(AssetKey("Orders_Dataset")).get_asset_spec(
            AssetKey("Orders_Dataset")
        )
        assert dataset_spec.tags.get("custom_tag") == "custom_value"
        assert dataset_spec.tags.get("is_dataset") == "true"


class CustomSigmaComponent(SigmaComponent):
    def get_asset_spec(self, data) -> AssetSpec:
        # Override to add custom metadata and tags
        base_spec = super().get_asset_spec(data)
        return base_spec.replace_attributes(
            metadata={**base_spec.metadata, "custom_override": "test_value"},
            tags={**base_spec.tags, "custom_tag": "override_test"},
        )


def test_subclass_override_get_asset_spec(sigma_sample_data: Any, sigma_auth_token: str) -> None:
    """Test that subclasses of SigmaComponent can override get_asset_spec method."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=CustomSigmaComponent,
            defs_yaml_contents={
                "type": "dagster_sigma_tests.test_components.CustomSigmaComponent",
                "attributes": {
                    "organization": {
                        "base_url": SigmaBaseUrl.AWS_US.value,
                        "client_id": uuid.uuid4().hex,
                        "client_secret": uuid.uuid4().hex,
                    },
                },
            },
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (_, defs),
        ):
            # Verify that the custom get_asset_spec method is being used
            assets_def = defs.get_assets_def(AssetKey("Sample_Workbook"))
            asset_spec = assets_def.get_asset_spec(AssetKey("Sample_Workbook"))

            # Check that our custom metadata and tags are present
            assert asset_spec.metadata["custom_override"] == "test_value"
            assert asset_spec.tags["custom_tag"] == "override_test"


@pytest.mark.parametrize(
    "defs_state_type",
    ["LOCAL_FILESYSTEM", "VERSIONED_STATE_STORAGE"],
)
def test_component_load_with_defs_state(
    sigma_sample_data: Any,
    sigma_auth_token: str,
    defs_state_type: str,
) -> None:
    import asyncio

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SigmaComponent,
            defs_yaml_contents={
                "type": "dagster_sigma.SigmaComponent",
                "attributes": {
                    "organization": {
                        "base_url": SigmaBaseUrl.AWS_US.value,
                        "client_id": uuid.uuid4().hex,
                        "client_secret": uuid.uuid4().hex,
                    },
                    "defs_state": {"management_type": defs_state_type},
                },
            },
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # First load, nothing there
            assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0
            assert isinstance(component, SigmaComponent)
            asyncio.run(component.refresh_state(sandbox.project_root))

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            # Second load, should now have assets
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
            assert AssetKey("Sample_Workbook") in asset_keys
            assert AssetKey("Orders_Dataset") in asset_keys
