from unittest.mock import MagicMock

import dagster as dg
import pytest

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
from dagster_aws.redshift.resources import RedshiftClientResource
from dagster_aws.s3.resources import S3Resource
from dagster_aws.ssm.resources import ParameterStoreResource, ParameterStoreTag, SSMResource
from dagster_aws.utils import ResourceWithBoto3Configuration

# --- Section 1: Metadata & Field Sync Tests ---


@pytest.mark.parametrize(
    "component_class, resource_class",
    [
        (Boto3CredentialsComponent, ResourceWithBoto3Configuration),
        (S3CredentialsComponent, S3Resource),
        (AthenaCredentialsComponent, ResourceWithAthenaConfig),
        (RedshiftCredentialsComponent, RedshiftClientResource),
    ],
)
def test_component_fields_sync_with_resource(component_class, resource_class):
    """Ensure component configuration fields stay in sync with the original resource classes.
    This covers 4 different credential/resource types.
    """
    component_fields = set(component_class.model_fields.keys())
    resource_fields = set(resource_class.model_fields.keys())

    assert resource_fields.issubset(component_fields), (
        f"Missing fields in {component_class.__name__}: {resource_fields - component_fields}"
    )


# --- Section 2: S3 Component Tests ---


def test_s3_resource_load_and_fields():
    """Verify S3 component correctly instantiates resource with specific fields."""
    creds = S3CredentialsComponent(region_name="us-east-1", max_attempts=5)
    component = S3ResourceComponent(credentials=creds, resource_key="my_s3")

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert defs.resources is not None
    resource = defs.resources["my_s3"]

    assert isinstance(resource, S3Resource)
    assert resource.region_name == "us-east-1"
    assert resource.max_attempts == 5


def test_s3_resource_default_key():
    """Verify that S3 component uses the default 's3' key when omitted."""
    component = S3ResourceComponent(credentials="{{ env_var('AWS_CREDS') }}")
    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert defs.resources is not None
    assert "s3" in defs.resources
    assert isinstance(defs.resources["s3"], S3Resource)


# --- Section 3: Athena Component Tests ---


def test_athena_resource_load():
    """Verify Athena component correctly instantiates its resource."""
    creds = AthenaCredentialsComponent(workgroup="test_wg", region_name="us-west-2")
    component = AthenaClientResourceComponent(credentials=creds)

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert defs.resources is not None
    resource = defs.resources["athena"]

    assert isinstance(resource, AthenaClientResource)
    assert resource.workgroup == "test_wg"


# --- Section 4: Redshift Component Tests ---


def test_redshift_resource_load():
    """Verify Redshift component correctly instantiates its resource with connection details."""
    creds = RedshiftCredentialsComponent(host="my-cluster", database="dev", user="admin")
    component = RedshiftClientResourceComponent(credentials=creds, resource_key="my_redshift")

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert defs.resources is not None
    resource = defs.resources["my_redshift"]

    assert isinstance(resource, RedshiftClientResource)
    assert resource.host == "my-cluster"


def test_redshift_template_error_handling():
    """Verify Redshift raises a ValueError when a raw template is used (missing connection details)."""
    component = RedshiftClientResourceComponent(credentials="{{ env_var('REDSHIFT_URL') }}")

    with pytest.raises(ValueError, match="Redshift credentials cannot be a raw string template"):
        _ = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))


# --- Section 5: SSM & Parameter Store Tests ---


def test_ssm_resource_load():
    """Verify standard SSM component load."""
    creds = Boto3CredentialsComponent(region_name="us-east-1")
    component = SSMResourceComponent(credentials=creds)

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert defs.resources is not None
    resources = defs.resources
    assert isinstance(resources["ssm"], SSMResource)


def test_parameter_store_resource_and_tags():
    """Verify Parameter Store component load and nested tag resolution."""
    creds = Boto3CredentialsComponent(region_name="us-east-1")
    tags = [ParameterStoreTag(key="Project", values=["Dagster"])]

    component = ParameterStoreResourceComponent(
        credentials=creds, parameters=["/prod/db/url"], resource_key="ps"
    )

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert defs.resources is not None
    resource = defs.resources["ps"]

    assert isinstance(resource, ParameterStoreResource)
    assert resource.parameters == ["/prod/db/url"]
    assert tags[0].key == "Project"


# --- Section 6: General Architecture Tests (Templates & Objects) ---


def test_direct_credential_object_resolution():
    """Verify that passing a typed Credential object is correctly handled."""
    creds = S3CredentialsComponent(region_name="eu-west-1")
    component = S3ResourceComponent(credentials=creds)

    assert isinstance(component.credentials, Boto3CredentialsComponent)
    assert component.credentials.region_name == "eu-west-1"


def test_string_template_fallback_logic():
    """Verify that string templates allow the component to return a default resource instance."""
    component = S3ResourceComponent(credentials="{{ my_template }}")

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    # Should not crash and should produce an S3Resource
    assert defs.resources is not None
    assert isinstance(defs.resources["s3"], S3Resource)


def test_custom_resource_key_override():
    """Verify that a user-provided resource_key overrides any default value."""
    creds = S3CredentialsComponent(region_name="us-east-1")
    component = S3ResourceComponent(credentials=creds, resource_key="my_custom_key")

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert defs.resources is not None
    assert "my_custom_key" in defs.resources
    assert "s3" not in defs.resources
