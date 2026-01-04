from typing import get_args, get_origin

import pytest
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox

from dagster_aws.athena.resources import AthenaClientResource, ResourceWithAthenaConfig
from dagster_aws.components import (
    AthenaClientResourceComponent,
    AthenaCredentialsComponent,
    Boto3CredentialsComponent,
    ParameterStoreResourceComponent,
    RDSResourceComponent,
    RedshiftClientResourceComponent,
    RedshiftCredentialsComponent,
    S3CredentialsComponent,
    S3FileManagerComponent,
    S3ResourceComponent,
    SecretsManagerResourceComponent,
    SecretsManagerSecretsResourceComponent,
    SSMResourceComponent,
)
from dagster_aws.rds.resources import RDSResource
from dagster_aws.redshift.resources import RedshiftClientResource
from dagster_aws.s3.file_manager import S3FileManager
from dagster_aws.s3.resources import S3Resource
from dagster_aws.secretsmanager.resources import (
    SecretsManagerResource,
    SecretsManagerSecretsResource,
)
from dagster_aws.ssm.resources import ParameterStoreResource, SSMResource
from dagster_aws.utils import ResourceWithBoto3Configuration

# --- Field Sync Tests ---


@pytest.mark.parametrize(
    "component_class, resource_class",
    [
        (Boto3CredentialsComponent, ResourceWithBoto3Configuration),
        (S3CredentialsComponent, S3Resource),
        (AthenaCredentialsComponent, ResourceWithAthenaConfig),
        (RedshiftCredentialsComponent, RedshiftClientResource),
        (S3ResourceComponent, S3Resource),
        (AthenaClientResourceComponent, AthenaClientResource),
        (RedshiftClientResourceComponent, RedshiftClientResource),
        (SSMResourceComponent, SSMResource),
        (ParameterStoreResourceComponent, ParameterStoreResource),
        (SecretsManagerResourceComponent, SecretsManagerResource),
        (SecretsManagerSecretsResourceComponent, SecretsManagerSecretsResource),
        (RDSResourceComponent, RDSResource),
    ],
)
def test_component_fields_sync_with_resource(component_class, resource_class):
    """Ensure component configuration fields stay in sync with the original resource classes."""
    component_fields = set(component_class.model_fields.keys())

    if "credentials" in component_class.model_fields:
        creds_field = component_class.model_fields["credentials"]
        creds_annotation = creds_field.annotation
        origin = get_origin(creds_annotation)
        if origin:
            args = get_args(creds_annotation)
            actual_creds_class = next((arg for arg in args if hasattr(arg, "model_fields")), None)
        else:
            actual_creds_class = creds_annotation

        if actual_creds_class and hasattr(actual_creds_class, "model_fields"):
            component_fields.update(actual_creds_class.model_fields.keys())

    resource_fields = set(resource_class.model_fields.keys())
    missing = resource_fields - component_fields
    assert resource_fields.issubset(component_fields), (
        f"Missing fields in {component_class.__name__}: {missing}"
    )


# --- S3 Component Tests ---


def test_s3_component_integration(monkeypatch):
    """Verifies that the S3 component can be loaded from YAML and correctly resolves
    environment variables using {{ env.VAR }} syntax.
    """
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("MAX_ATTEMPTS", "5")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=S3ResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.S3ResourceComponent",
                "attributes": {
                    "credentials": {
                        "region_name": "{{ env.AWS_REGION }}",
                        "max_attempts": "{{ env.MAX_ATTEMPTS }}",
                    },
                    "resource_key": "my_s3",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert isinstance(defs.resources["my_s3"], S3Resource)
                assert defs.resources["my_s3"].region_name == "us-east-1"
                assert defs.resources["my_s3"].max_attempts == 5


def test_s3_default_key_behavior():
    """Verifies that if 'resource_key' is omitted in the YAML, the component
    defaults to registering the resource under 's3'.
    """
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=S3ResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.S3ResourceComponent",
                "attributes": {"credentials": {"region_name": "us-east-1"}},
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert "s3" in defs.resources
                assert isinstance(defs.resources["s3"], S3Resource)


def test_s3_file_manager_integration(monkeypatch):
    """Full integration test for S3FileManagerComponent."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("MY_BUCKET", "test-bucket-artifacts")
    monkeypatch.setenv("MY_PREFIX", "dagster/logs")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=S3FileManagerComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.S3FileManagerComponent",
                "attributes": {
                    "credentials": {"region_name": "{{ env.AWS_REGION }}"},
                    "s3_bucket": "{{ env.MY_BUCKET }}",
                    "s3_prefix": "{{ env.MY_PREFIX }}",
                    "resource_key": "my_file_manager",
                },
            },
        )

        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert "my_file_manager" in defs.resources
                resource = defs.resources["my_file_manager"]
                assert isinstance(resource, S3FileManager)


# --- Athena Component Tests ---


def test_athena_component_integration(monkeypatch):
    """Verifies proper loading of Athena component with nested credentials."""
    monkeypatch.setenv("ATHENA_WORKGROUP", "primary")
    monkeypatch.setenv("AWS_REGION", "us-west-2")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=AthenaClientResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.AthenaClientResourceComponent",
                "attributes": {
                    "credentials": {
                        "region_name": "{{ env.AWS_REGION }}",
                        "workgroup": "{{ env.ATHENA_WORKGROUP }}",
                    }
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert defs.resources["athena"].workgroup == "primary"


# --- Redshift Component Tests ---


def test_redshift_component_integration(monkeypatch):
    """Verifies Redshift component loading and type conversion (string env var to int port)."""
    monkeypatch.setenv("REDSHIFT_HOST", "cluster.redshift.amazonaws.com")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=RedshiftClientResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.RedshiftClientResourceComponent",
                "attributes": {
                    "credentials": {
                        "host": "{{ env.REDSHIFT_HOST }}",
                        "port": 5439,
                        "database": "dev",
                        "user": "admin",
                    }
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert defs.resources["redshift"].host == "cluster.redshift.amazonaws.com"
                assert defs.resources["redshift"].port == 5439


# --- SSM Component Tests ---


def test_ssm_component_integration(monkeypatch):
    """Verifies SSM component loading."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SSMResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.SSMResourceComponent",
                "attributes": {"credentials": {"region_name": "{{ env.AWS_REGION }}"}},
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert defs.resources["ssm"].region_name == "us-east-1"


# --- Parameter Store Component Tests ---


def test_parameter_store_defaults_behavior():
    """Verifies that 'parameters' defaults to an empty list if not specified in YAML."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ParameterStoreResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.ParameterStoreResourceComponent",
                "attributes": {"credentials": {"region_name": "us-east-1"}},
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert defs.resources["parameter_store"].parameters == []


def test_parameter_store_complex_integration(monkeypatch):
    """Verifies Parameter Store component handling of list fields and booleans."""
    monkeypatch.setenv("AWS_REGION", "us-west-1")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ParameterStoreResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.ParameterStoreResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "{{ env.AWS_REGION }}"},
                    "parameters": ["/app/db/password"],
                    "with_decryption": True,
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                res = defs.resources["parameter_store"]
                assert res.region_name == "us-west-1"
                assert res.parameters == ["/app/db/password"]
                assert res.with_decryption is True


# --- Secrets Manager Component Tests ---


def test_secrets_manager_integration(monkeypatch):
    """Verifies Secrets Manager (Client) component loading."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SecretsManagerResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.SecretsManagerResourceComponent",
                "attributes": {"credentials": {"region_name": "{{ env.AWS_REGION }}"}},
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert isinstance(defs.resources["secretsmanager"], SecretsManagerResource)
                assert defs.resources["secretsmanager"].region_name == "us-east-1"


def test_secrets_manager_secrets_integration(monkeypatch):
    """Verifies Secrets Manager (Fetcher) component loading, including list resolution."""
    monkeypatch.setenv("SECRET_ARN", "arn:aws:secretsmanager:us-east-1:123:secret:db")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SecretsManagerSecretsResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.SecretsManagerSecretsResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "us-east-1"},
                    "secrets": ["{{ env.SECRET_ARN }}"],
                    "resource_key": "my_secrets",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert defs.resources["my_secrets"].secrets == [
                    "arn:aws:secretsmanager:us-east-1:123:secret:db"
                ]


# --- RDS Component Tests ---


def test_rds_component_integration(monkeypatch):
    """Verifies RDS component loading."""
    monkeypatch.setenv("RDS_ENDPOINT", "https://rds.amazonaws.com")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=RDSResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.RDSResourceComponent",
                "attributes": {
                    "credentials": {
                        "endpoint_url": "{{ env.RDS_ENDPOINT }}",
                        "region_name": "{{ env.AWS_REGION }}",
                    },
                    "resource_key": "production_db",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert isinstance(defs.resources["production_db"], RDSResource)
                assert defs.resources["production_db"].endpoint_url == "https://rds.amazonaws.com"
