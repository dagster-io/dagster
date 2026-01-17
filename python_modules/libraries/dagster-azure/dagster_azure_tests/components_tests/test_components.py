import pytest
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster.components.testing import create_defs_folder_sandbox

from dagster_azure.adls2.io_manager import ADLS2PickleIOManager
from dagster_azure.adls2.resources import ADLS2Resource
from dagster_azure.blob.resources import AzureBlobStorageResource
from dagster_azure.components.adls2 import ADLS2ResourceComponent
from dagster_azure.components.blob import AzureBlobStorageResourceComponent
from dagster_azure.components.io_managers import ADLS2PickleIOManagerComponent


@pytest.mark.parametrize(
    "component_cls, resource_cls",
    [
        (AzureBlobStorageResourceComponent, AzureBlobStorageResource),
        (ADLS2ResourceComponent, ADLS2Resource),
    ],
)
def test_component_fields_match_resource(component_cls, resource_cls):
    """
    Ensures that the fields on the Component match the fields on the underlying Resource.
    """
    component_fields = set(component_cls.model_fields.keys())

    component_fields.discard("resource_key")
    component_fields.discard("type")

    resource_init_params = set(resource_cls.__init__.__annotations__.keys())
    resource_init_params.discard("return")

    missing_in_component = resource_init_params - component_fields
    assert not missing_in_component, (
        f"Component {component_cls.__name__} is missing fields present in Resource {resource_cls.__name__}: {missing_in_component}"
    )

    extra_in_component = component_fields - resource_init_params
    assert not extra_in_component, (
        f"Component {component_cls.__name__} has extra fields not in Resource {resource_cls.__name__}: {extra_in_component}"
    )


def test_blob_storage_component_yaml():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=AzureBlobStorageResourceComponent,
            defs_yaml_contents={
                "type": "dagster_azure.AzureBlobStorageResourceComponent",
                "attributes": {
                    "account_url": "https://myaccount.blob.core.windows.net",
                    "credential": {"credential_type": "sas", "sas_token": "test-token"},
                    "resource_key": "blob_storage",
                },
            },
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            assert "blob_storage" in defs.resources
            resource = defs.resources["blob_storage"]

            assert isinstance(resource, AzureBlobStorageResource)
            assert resource.account_url == "https://myaccount.blob.core.windows.net"


def test_adls2_component_yaml():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ADLS2ResourceComponent,
            defs_yaml_contents={
                "type": "dagster_azure.ADLS2ResourceComponent",
                "attributes": {
                    "storage_account": "mystorageaccount",
                    "credential": {"credential_type": "key", "storage_account_key": "fake-key"},
                    "resource_key": "adls2",
                },
            },
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            assert "adls2" in defs.resources
            resource = defs.resources["adls2"]

            assert isinstance(resource, ADLS2Resource)
            assert resource.storage_account == "mystorageaccount"


def test_adls2_io_manager_component_yaml():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ADLS2PickleIOManagerComponent,
            defs_yaml_contents={
                "type": "dagster_azure.ADLS2PickleIOManagerComponent",
                "attributes": {
                    "adls2": {
                        "storage_account": "io-storage",
                        "credential": {"credential_type": "key", "storage_account_key": "key"},
                    },
                    "adls2_file_system": "dagster-data",
                    "adls2_prefix": "io_manager_test",
                    "lease_duration": 30,
                    "resource_key": "io_manager",
                },
            },
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            assert "io_manager" in defs.resources
            io_manager = defs.resources["io_manager"]

            assert isinstance(io_manager, ADLS2PickleIOManager)
            assert io_manager.adls2_prefix == "io_manager_test"
            assert io_manager.adls2.storage_account == "io-storage"
