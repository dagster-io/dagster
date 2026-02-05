from typing import get_args, get_origin

import pytest
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox

from dagster_aws.athena.resources import AthenaClientResource, ResourceWithAthenaConfig
from dagster_aws.components import (
    AthenaClientResourceComponent,
    AthenaCredentialsComponent,
    Boto3CredentialsComponent,
    ECRPublicResourceComponent,
    ParameterStoreResourceComponent,
    RDSResourceComponent,
    S3CredentialsComponent,
    S3FileManagerResourceComponent,
    S3ResourceComponent,
    SecretsManagerResourceComponent,
    SecretsManagerSecretsResourceComponent,
    SSMResourceComponent,
)
from dagster_aws.ecr import ECRPublicResource
from dagster_aws.rds.resources import RDSResource
from dagster_aws.redshift import RedshiftClientResourceComponent, RedshiftCredentialsComponent
from dagster_aws.redshift.resources import RedshiftClientResource
from dagster_aws.s3.resources import S3FileManagerResource, S3Resource
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
        (S3FileManagerResourceComponent, S3FileManagerResource),
        (AthenaClientResourceComponent, AthenaClientResource),
        (RedshiftClientResourceComponent, RedshiftClientResource),
        (SSMResourceComponent, SSMResource),
        (ParameterStoreResourceComponent, ParameterStoreResource),
        (SecretsManagerResourceComponent, SecretsManagerResource),
        (SecretsManagerSecretsResourceComponent, SecretsManagerSecretsResource),
        (RDSResourceComponent, RDSResource),
        (ECRPublicResourceComponent, ECRPublicResource),
    ],
)
def test_component_fields_sync_with_resource(component_class, resource_class):
    """Validates that component configuration schemas are fully synchronized with their underlying resource definitions."""
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
    """Verifies successful instantiation of S3Resource from YAML with environment variable resolution."""
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
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert isinstance(defs.resources["my_s3"], S3Resource)
                assert defs.resources["my_s3"].region_name == "us-east-1"
                assert defs.resources["my_s3"].max_attempts == 5


def test_s3_no_resource_key():
    """Verifies that when resource_key is not provided, the resources dict is empty."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=S3ResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.S3ResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "us-east-1"},
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources == {}


def test_s3_explicit_key():
    """Verifies that the component registers correctly when resource_key is provided."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=S3ResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.S3ResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "us-east-1"},
                    "resource_key": "s3",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert "s3" in defs.resources
                assert isinstance(defs.resources["s3"], S3Resource)


def test_s3_file_manager_integration(monkeypatch):
    """Validates S3FileManagerResourceComponent instantiation and parameter mapping."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("MY_BUCKET", "test-bucket-artifacts")
    monkeypatch.setenv("MY_PREFIX", "dagster/logs")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=S3FileManagerResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.S3FileManagerResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "{{ env.AWS_REGION }}"},
                    "s3_bucket": "{{ env.MY_BUCKET }}",
                    "s3_prefix": "{{ env.MY_PREFIX }}",
                    "resource_key": "my_file_manager",
                },
            },
        )

        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert "my_file_manager" in defs.resources
                resource = defs.resources["my_file_manager"]
                assert isinstance(resource, S3FileManagerResource)
                assert resource.s3_bucket == "test-bucket-artifacts"
                assert resource.s3_prefix == "dagster/logs"
                assert resource.region_name == "us-east-1"


# --- Athena Component Tests ---


def test_athena_component_integration(monkeypatch):
    """Verifies AthenaClientResource loading with nested credentials configuration."""
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
                    },
                    "resource_key": "athena",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert defs.resources["athena"].workgroup == "primary"


# --- Redshift Component Tests ---


def test_redshift_component_integration(monkeypatch):
    """Verifies RedshiftClientResource loading and type conversion (string env vars to integer ports)."""
    monkeypatch.setenv("REDSHIFT_HOST", "cluster.redshift.amazonaws.com")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=RedshiftClientResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.redshift.RedshiftClientResourceComponent",
                "attributes": {
                    "credentials": {
                        "host": "{{ env.REDSHIFT_HOST }}",
                        "port": 5439,
                        "database": "dev",
                        "user": "admin",
                    },
                    "resource_key": "redshift",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert defs.resources["redshift"].host == "cluster.redshift.amazonaws.com"
                assert defs.resources["redshift"].port == 5439


# --- SSM Component Tests ---


def test_ssm_component_integration(monkeypatch):
    """Verifies SSMResource loading with basic regional configuration."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SSMResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.SSMResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "{{ env.AWS_REGION }}"},
                    "resource_key": "ssm",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert defs.resources["ssm"].region_name == "us-east-1"


# --- Parameter Store Component Tests ---


def test_parameter_store_defaults_behavior():
    """Verifies that ParameterStoreResource defaults to an empty parameter list when not specified."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ParameterStoreResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.ParameterStoreResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "us-east-1"},
                    "resource_key": "parameter_store",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert defs.resources["parameter_store"].parameters == []


def test_parameter_store_complex_integration(monkeypatch):
    """Verifies ParameterStoreResource handling of complex types (lists) and boolean flags."""
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
                    "resource_key": "parameter_store",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                res = defs.resources["parameter_store"]
                assert res.region_name == "us-west-1"
                assert res.parameters == ["/app/db/password"]
                assert res.with_decryption is True


# --- Secrets Manager Component Tests ---


def test_secrets_manager_integration(monkeypatch):
    """Verifies SecretsManagerResource (Client) instantiation from configuration."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SecretsManagerResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.SecretsManagerResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "{{ env.AWS_REGION }}"},
                    "resource_key": "secretsmanager",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert isinstance(defs.resources["secretsmanager"], SecretsManagerResource)
                assert defs.resources["secretsmanager"].region_name == "us-east-1"


def test_secrets_manager_secrets_integration(monkeypatch):
    """Verifies SecretsManagerSecretsResource loads specific secret ARNs correctly from YAML."""
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
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert defs.resources["my_secrets"].secrets == [
                    "arn:aws:secretsmanager:us-east-1:123:secret:db"
                ]


# --- RDS Component Tests ---


def test_rds_component_integration(monkeypatch):
    """Verifies RDSResource loading with endpoint URL and region configuration."""
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
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert isinstance(defs.resources["production_db"], RDSResource)
                assert defs.resources["production_db"].endpoint_url == "https://rds.amazonaws.com"


# --- ECR Component Tests ---


def test_ecr_public_component_integration(monkeypatch):
    """Verifies ECRPublicResource instantiation via the Dagster Sandbox."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ECRPublicResourceComponent,
            defs_yaml_contents={
                "type": "dagster_aws.components.ECRPublicResourceComponent",
                "attributes": {
                    "credentials": {"region_name": "{{ env.AWS_REGION }}"},
                    "resource_key": "public_ecr",
                },
            },
        )
        with scoped_definitions_load_context():
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (_component, defs):
                assert defs.resources
                assert "public_ecr" in defs.resources
                resource = defs.resources["public_ecr"]
                assert isinstance(resource, ECRPublicResource)
