from typing import get_args, get_origin

import pytest
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster_gcp.bigquery.resources import BigQueryResource
from dagster_gcp.components import (
    BigQueryResourceComponent,
    DataprocResourceComponent,
    GCSFileManagerResourceComponent,
    GCSPickleIOManagerComponent,
    GCSResourceComponent,
)
from dagster_gcp.dataproc.resources import DataprocResource
from dagster_gcp.gcs.io_manager import GCSPickleIOManager
from dagster_gcp.gcs.resources import GCSFileManagerResource, GCSResource


class TestComponentFieldsSync:
    """Tests that component fields are synchronized with their underlying resource definitions."""

    @pytest.mark.parametrize(
        "component_class, resource_class, exclude_fields",
        [
            (BigQueryResourceComponent, BigQueryResource, {"gcp_credentials"}),
            (GCSResourceComponent, GCSResource, {"gcp_credentials"}),
            (GCSFileManagerResourceComponent, GCSFileManagerResource, {"gcp_credentials"}),
            (GCSPickleIOManagerComponent, GCSPickleIOManager, {"gcs"}),
            (DataprocResourceComponent, DataprocResource, set()),
        ],
    )
    def test_component_fields_sync_with_resource(
        self, component_class, resource_class, exclude_fields
    ):
        """Validates that component configuration schemas are fully synchronized with their underlying resource definitions."""
        component_fields = set(component_class.model_fields.keys())
        resource_fields = set(resource_class.model_fields.keys())

        # Handle nested field structures if present
        if "credentials" in component_class.model_fields:
            creds_field = component_class.model_fields["credentials"]
            creds_annotation = creds_field.annotation
            origin = get_origin(creds_annotation)
            if origin:
                args = get_args(creds_annotation)
                actual_creds_class = next(
                    (arg for arg in args if hasattr(arg, "model_fields")), None
                )
            else:
                actual_creds_class = creds_annotation

            if actual_creds_class and hasattr(actual_creds_class, "model_fields"):
                component_fields.update(actual_creds_class.model_fields.keys())

        resource_fields = resource_fields - exclude_fields

        missing = resource_fields - component_fields
        assert resource_fields.issubset(component_fields), (
            f"Missing fields in {component_class.__name__}: {missing}"
        )


class TestYAMLIntegration:
    """Tests for YAML-based component instantiation and definition loading."""

    def test_bigquery_component_yaml(self):
        """Verifies successful instantiation of BigQueryResource from YAML."""
        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=BigQueryResourceComponent,
                defs_yaml_contents={
                    "type": "dagster_gcp.components.BigQueryResourceComponent",
                    "attributes": {
                        "project": "my-project",
                        "location": "us-west1",
                        "resource_key": "my_bigquery",
                    },
                },
            )
            with scoped_definitions_load_context():
                with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                    component,
                    defs,
                ):
                    assert defs.resources
                    assert "my_bigquery" in defs.resources
                    resource = defs.resources["my_bigquery"]
                    assert isinstance(resource, BigQueryResource)
                    assert resource.project == "my-project"
                    assert resource.location == "us-west1"

    def test_bigquery_component_yaml_minimal(self):
        """Verifies BigQueryResource with minimal configuration (allows ADC fallback)."""
        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=BigQueryResourceComponent,
                defs_yaml_contents={
                    "type": "dagster_gcp.components.BigQueryResourceComponent",
                    "attributes": {
                        "resource_key": "bigquery_default",
                    },
                },
            )
            with scoped_definitions_load_context():
                with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                    component,
                    defs,
                ):
                    assert defs.resources
                    assert "bigquery_default" in defs.resources
                    resource = defs.resources["bigquery_default"]
                    assert isinstance(resource, BigQueryResource)
                    assert resource.project is None

    def test_gcs_component_yaml(self):
        """Verifies successful instantiation of GCSResource from YAML."""
        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=GCSResourceComponent,
                defs_yaml_contents={
                    "type": "dagster_gcp.components.GCSResourceComponent",
                    "attributes": {
                        "project": "my-gcp-project",
                        "resource_key": "my_gcs",
                    },
                },
            )
            with scoped_definitions_load_context():
                with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                    component,
                    defs,
                ):
                    assert defs.resources
                    assert "my_gcs" in defs.resources
                    resource = defs.resources["my_gcs"]
                    assert isinstance(resource, GCSResource)
                    assert resource.project == "my-gcp-project"

    def test_gcs_file_manager_component_yaml(self):
        """Verifies successful instantiation of GCSFileManagerResource from YAML."""
        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=GCSFileManagerResourceComponent,
                defs_yaml_contents={
                    "type": "dagster_gcp.components.GCSFileManagerResourceComponent",
                    "attributes": {
                        "project": "my-gcp-project",
                        "gcs_bucket": "my-bucket",
                        "gcs_prefix": "dagster/data",
                        "resource_key": "my_file_manager",
                    },
                },
            )
            with scoped_definitions_load_context():
                with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                    component,
                    defs,
                ):
                    assert defs.resources
                    assert "my_file_manager" in defs.resources
                    resource = defs.resources["my_file_manager"]
                    assert isinstance(resource, GCSFileManagerResource)
                    assert resource.project == "my-gcp-project"
                    assert resource.gcs_bucket == "my-bucket"
                    assert resource.gcs_prefix == "dagster/data"

    def test_io_manager_component_yaml(self):
        """Verifies successful instantiation of GCSPickleIOManager from YAML."""
        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=GCSPickleIOManagerComponent,
                defs_yaml_contents={
                    "type": "dagster_gcp.components.GCSPickleIOManagerComponent",
                    "attributes": {
                        "gcs_bucket": "my-io-bucket",
                        "gcs_prefix": "custom/prefix",
                        "project": "my-project",
                        "resource_key": "io_manager",
                    },
                },
            )
            with scoped_definitions_load_context():
                with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                    component,
                    defs,
                ):
                    assert defs.resources
                    assert "io_manager" in defs.resources
                    resource = defs.resources["io_manager"]
                    assert isinstance(resource, GCSPickleIOManager)
                    assert resource.gcs_bucket == "my-io-bucket"
                    assert resource.gcs_prefix == "custom/prefix"
                    assert resource.gcs.project == "my-project"

    def test_dataproc_component_yaml(self):
        """Verifies successful instantiation of DataprocResource from YAML."""
        cluster_config = {
            "masterConfig": {"machineTypeUri": "n1-standard-4"},
            "workerConfig": {"machineTypeUri": "n1-standard-4", "numInstances": 3},
        }

        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=DataprocResourceComponent,
                defs_yaml_contents={
                    "type": "dagster_gcp.components.DataprocResourceComponent",
                    "attributes": {
                        "project_id": "my-project",
                        "region": "us-central1",
                        "cluster_name": "my-cluster",
                        "cluster_config_dict": cluster_config,
                        "resource_key": "my_dataproc",
                    },
                },
            )
            with scoped_definitions_load_context():
                with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                    component,
                    defs,
                ):
                    assert defs.resources
                    assert "my_dataproc" in defs.resources
                    resource = defs.resources["my_dataproc"]
                    assert isinstance(resource, DataprocResource)
                    assert resource.project_id == "my-project"

    def test_component_without_resource_key(self):
        """Verifies that components without resource_key don't register resources."""
        with create_defs_folder_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=BigQueryResourceComponent,
                defs_yaml_contents={
                    "type": "dagster_gcp.components.BigQueryResourceComponent",
                    "attributes": {
                        "project": "my-project",
                    },
                },
            )
            with scoped_definitions_load_context():
                with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                    component,
                    defs,
                ):
                    assert not defs.resources
