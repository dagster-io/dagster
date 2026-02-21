from typing import get_args, get_origin

import pytest
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster_azure.adls2.resources import ADLS2Resource
from dagster_azure.blob.resources import AzureBlobStorageResource
from dagster_azure.components.adls2 import ADLS2ResourceComponent
from dagster_azure.components.blob import AzureBlobStorageResourceComponent


@pytest.mark.parametrize(
    "component_class, resource_class",
    [
        (AzureBlobStorageResourceComponent, AzureBlobStorageResource),
        (ADLS2ResourceComponent, ADLS2Resource),
    ],
)
def test_component_fields_sync_with_resource(component_class, resource_class):
    """Verify that the component fields stay in sync with the underlying resource fields.
    This prevents 'drift' where new fields added to the resource are missing from the component.
    """
    component_fields = set(component_class.model_fields.keys())

    # If a credential field exists, include nested fields from the union of credentials
    if "credential" in component_class.model_fields:
        creds_field = component_class.model_fields["credential"]
        creds_annotation = creds_field.annotation
        origin = get_origin(creds_annotation)
        if origin:
            args = get_args(creds_annotation)
            for arg in args:
                if hasattr(arg, "model_fields"):
                    component_fields.update(arg.model_fields.keys())
        elif hasattr(creds_annotation, "model_fields"):
            component_fields.update(creds_annotation.model_fields.keys())

    # Remove technical component fields that are not present in the underlying resources
    component_fields.discard("credential_type")
    component_fields.discard("resource_key")
    component_fields.discard("type")

    resource_fields = set(resource_class.model_fields.keys())
    resource_fields.discard("credential")

    missing = resource_fields - component_fields
    assert resource_fields.issubset(component_fields), (
        f"Missing fields in {component_class.__name__}: {missing}"
    )


def test_blob_storage_component_integration(monkeypatch):
    """Test YAML-based instantiation for the Azure Blob Storage component.
    Ensures that credentials and URLs are correctly resolved from environment variables.
    """
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", "https://myaccount.blob.core.windows.net")
    monkeypatch.setenv("AZURE_STORAGE_KEY", "fake-key")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=AzureBlobStorageResourceComponent,
            defs_yaml_contents={
                "type": "dagster_azure.AzureBlobStorageResourceComponent",
                "attributes": {
                    "account_url": "{{ env.AZURE_STORAGE_ACCOUNT_URL }}",
                    "credential": {
                        "credential_type": "key",
                        "key": "{{ env.AZURE_STORAGE_KEY }}",
                    },
                    "resource_key": "my_blob",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_, defs):
                resources = defs.resources
                # Assertions to satisfy Pyright and verify resource creation
                assert resources is not None
                assert "my_blob" in resources
                resource = resources["my_blob"]
                assert isinstance(resource, AzureBlobStorageResource)


def test_adls2_component_integration(monkeypatch):
    """Test YAML-based instantiation for the ADLS2 Resource component.
    Verifies the handling of the ADLS2-specific credential union (SAS token).
    """
    monkeypatch.setenv("ADLS2_STORAGE_ACCOUNT", "myadlsaccount")
    monkeypatch.setenv("ADLS2_SAS_TOKEN", "fake-sas-token")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ADLS2ResourceComponent,
            defs_yaml_contents={
                "type": "dagster_azure.ADLS2ResourceComponent",
                "attributes": {
                    "storage_account": "{{ env.ADLS2_STORAGE_ACCOUNT }}",
                    "credential": {
                        "credential_type": "sas",
                        "token": "{{ env.ADLS2_SAS_TOKEN }}",
                    },
                    "resource_key": "my_adls2",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_, defs):
                resources = defs.resources
                assert resources is not None
                assert "my_adls2" in resources
                resource = resources["my_adls2"]
                assert isinstance(resource, ADLS2Resource)
