import os
from typing import get_args, get_origin
from unittest.mock import MagicMock

import dagster as dg
import jinja2
import pytest
import yaml

from dagster_aws.athena.resources import AthenaClientResource, ResourceWithAthenaConfig
from dagster_aws.components import (
    AthenaClientResourceComponent,
    AthenaCredentialsComponent,
    Boto3CredentialsComponent,
    ParameterStoreResourceComponent,
    RedshiftClientResourceComponent,
    RedshiftCredentialsComponent,
    S3CredentialsComponent,
    S3ResourceComponent,
    SSMResourceComponent,
)
from dagster_aws.components.secretsmanager import (
    SecretsManagerResourceComponent,
    SecretsManagerSecretsResourceComponent,
)
from dagster_aws.redshift.resources import RedshiftClientResource
from dagster_aws.s3.resources import S3Resource
from dagster_aws.secretsmanager.resources import (
    SecretsManagerResource,
    SecretsManagerSecretsResource,
)
from dagster_aws.ssm.resources import ParameterStoreResource, SSMResource
from dagster_aws.utils import ResourceWithBoto3Configuration


def load_component_defs(yaml_content: str, component_class) -> dg.Definitions:
    """Simulates the Dagster component loading process."""
    template = jinja2.Template(yaml_content)
    rendered_yaml = template.render(env_var=lambda key: os.environ.get(key, ""))
    config = yaml.safe_load(rendered_yaml)

    component = component_class(**config)
    return component.build_defs(MagicMock(spec=dg.ComponentLoadContext))


@pytest.mark.parametrize(
    "component_class, resource_class",
    [
        # --- Credentials Components (Flat) ---
        (Boto3CredentialsComponent, ResourceWithBoto3Configuration),
        (S3CredentialsComponent, S3Resource),
        (AthenaCredentialsComponent, ResourceWithAthenaConfig),
        (RedshiftCredentialsComponent, RedshiftClientResource),
        # --- Service Components (Nested inside credentials) ---
        (S3ResourceComponent, S3Resource),
        (AthenaClientResourceComponent, AthenaClientResource),
        (RedshiftClientResourceComponent, RedshiftClientResource),
        (SSMResourceComponent, SSMResource),
        (ParameterStoreResourceComponent, ParameterStoreResource),
        (SecretsManagerResourceComponent, SecretsManagerResource),
        (SecretsManagerSecretsResourceComponent, SecretsManagerSecretsResource),
    ],
)
def test_component_fields_sync_with_resource(component_class, resource_class):
    """Ensure component configuration fields stay in sync with the original resource classes.
    Checks both direct fields and fields nested within 'credentials'.
    """
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
        f"Missing fields in {component_class.__name__}: {missing}. "
        "Make sure these fields are present either in the component or in its credentials."
    )


# --- S3 Component Tests ---


def test_s3_resource_load_from_yaml(monkeypatch):
    """Verify S3 component correctly resolves env vars and types via YAML loading."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("MAX_ATTEMPTS", "5")

    yaml_content = """
credentials:
  region_name: "{{ env_var('AWS_REGION') }}"
  max_attempts: "{{ env_var('MAX_ATTEMPTS') }}"
resource_key: "my_s3"
"""
    defs = load_component_defs(yaml_content, S3ResourceComponent)
    assert defs.resources is not None
    resource = defs.resources["my_s3"]

    assert isinstance(resource, S3Resource)
    assert resource.region_name == "us-east-1"
    assert resource.max_attempts == 5


def test_s3_resource_default_key():
    """Verify that S3 component uses the default 's3' key when omitted in YAML."""
    yaml_content = """
credentials:
  region_name: "us-east-1"
"""
    defs = load_component_defs(yaml_content, S3ResourceComponent)
    assert defs.resources is not None
    assert "s3" in defs.resources
    assert isinstance(defs.resources["s3"], S3Resource)


# --- Athena Component Tests ---


def test_athena_resource_load_from_yaml(monkeypatch):
    """Verify Athena component correctly resolves configuration from YAML."""
    monkeypatch.setenv("ATHENA_WORKGROUP", "test_wg")
    monkeypatch.setenv("AWS_REGION", "us-west-2")

    yaml_content = """
credentials:
  workgroup: "{{ env_var('ATHENA_WORKGROUP') }}"
  region_name: "{{ env_var('AWS_REGION') }}"
"""
    defs = load_component_defs(yaml_content, AthenaClientResourceComponent)
    assert defs.resources is not None
    resource = defs.resources["athena"]

    assert isinstance(resource, AthenaClientResource)
    assert resource.workgroup == "test_wg"


# --- Redshift Component Tests ---


def test_redshift_resource_load_from_yaml(monkeypatch):
    """Verify Redshift component correctly resolves strict types (int) from env vars."""
    monkeypatch.setenv("REDSHIFT_HOST", "my-cluster")
    monkeypatch.setenv("REDSHIFT_PORT", "5439")

    yaml_content = """
credentials:
  host: "{{ env_var('REDSHIFT_HOST') }}"
  port: "{{ env_var('REDSHIFT_PORT') }}"
  user: "admin"
  database: "dev"
resource_key: "my_redshift"
"""
    defs = load_component_defs(yaml_content, RedshiftClientResourceComponent)
    assert defs.resources is not None
    resource = defs.resources["my_redshift"]

    assert isinstance(resource, RedshiftClientResource)
    assert resource.host == "my-cluster"
    assert resource.port == 5439


# --- SSM & Parameter Store Tests ---
def test_ssm_resource_load_from_yaml(monkeypatch):
    """Verify SSM component correctly loads from YAML."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    yaml_content = """
credentials:
  region_name: "{{ env_var('AWS_REGION') }}"
"""
    defs = load_component_defs(yaml_content, SSMResourceComponent)
    assert defs.resources is not None
    assert isinstance(defs.resources["ssm"], SSMResource)


def test_parameter_store_defaults_from_yaml():
    """Verify default factory works (parameters defaults to empty list) when loading from YAML."""
    yaml_content = """
credentials:
  region_name: "us-east-1"
"""
    defs = load_component_defs(yaml_content, ParameterStoreResourceComponent)
    assert defs.resources is not None
    resource = defs.resources["parameter_store"]

    assert isinstance(resource, ParameterStoreResource)
    assert resource.parameters == []


def test_parameter_store_explicit_list_from_yaml():
    """Verify Parameter Store accepts an explicit list from YAML."""
    yaml_content = """
credentials:
  region_name: "us-east-1"
parameters:
  - "/prod/db/url"
  - "/prod/api/key"
"""
    defs = load_component_defs(yaml_content, ParameterStoreResourceComponent)
    assert defs.resources is not None
    resource = defs.resources["parameter_store"]

    assert resource.parameters == ["/prod/db/url", "/prod/api/key"]


def test_custom_resource_key_override():
    """Verify that a user-provided resource_key in YAML overrides the default."""
    yaml_content = """
credentials:
  region_name: "us-east-1"
resource_key: "custom_s3_bucket"
"""
    defs = load_component_defs(yaml_content, S3ResourceComponent)
    resources = defs.resources
    assert resources is not None
    assert "custom_s3_bucket" in resources
    assert "s3" not in resources


# --- Secrets Manager Component Tests ---


def test_secrets_manager_resource_load_from_yaml(monkeypatch):
    """Verify Secrets Manager client correctly resolves env vars."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    yaml_content = """
credentials:
  region_name: "{{ env_var('AWS_REGION') }}"
"""
    defs = load_component_defs(yaml_content, SecretsManagerResourceComponent)

    assert defs.resources is not None
    resource = defs.resources["secretsmanager"]

    assert isinstance(resource, SecretsManagerResource)
    assert resource.region_name == "us-east-1"


def test_secrets_manager_secrets_resource_load_from_yaml(monkeypatch):
    """Verify Secrets Manager fetcher correctly resolves lists and configs."""
    monkeypatch.setenv("MY_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:123:secret:prod-db")

    yaml_content = """
credentials:
  region_name: "us-east-1"
secrets:
  - "{{ env_var('MY_SECRET_ARN') }}"
  - "arn:aws:secretsmanager:us-east-1:123:secret:api-key"
resource_key: "my_secrets"
"""
    defs = load_component_defs(yaml_content, SecretsManagerSecretsResourceComponent)

    assert defs.resources is not None
    resource = defs.resources["my_secrets"]

    assert isinstance(resource, SecretsManagerSecretsResource)
    assert resource.secrets == [
        "arn:aws:secretsmanager:us-east-1:123:secret:prod-db",
        "arn:aws:secretsmanager:us-east-1:123:secret:api-key",
    ]
