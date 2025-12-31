from unittest.mock import MagicMock

import dagster as dg
import pytest

from dagster_aws.components import (
    Boto3CredentialsComponent,
    S3CredentialsComponent,
    S3ResourceComponent,
)
from dagster_aws.s3.resources import S3Resource
from dagster_aws.utils import ResourceWithBoto3Configuration


def test_s3_resource_component_load():
    """Test that S3ResourceComponent correctly instantiates an S3Resource with provided config."""
    config = {
        "credentials": {
            "region_name": "us-east-1",
            "max_attempts": 5,
        },
        "resource_key": "my_s3_resource",
    }

    component = S3ResourceComponent(**config)

    mock_context = MagicMock(spec=dg.ComponentLoadContext)
    defs = component.build_defs(mock_context)

    assert defs.resources is not None
    resource = defs.resources["my_s3_resource"]

    assert isinstance(resource, S3Resource)
    assert resource.region_name == "us-east-1"
    assert resource.max_attempts == 5


def test_credentials_resolution():
    """Test that the component correctly resolves a directly passed Credentials object."""
    raw_config = {"region_name": "eu-central-1"}
    creds = S3CredentialsComponent(**raw_config)

    component = S3ResourceComponent(credentials=creds, resource_key="s3")

    assert isinstance(component.credentials, Boto3CredentialsComponent)
    assert component.credentials.region_name == "eu-central-1"


def test_templated_credentials():
    """Test that the component supports string-based credentials (e.g., environment variables or templates)."""
    config = {
        "credentials": "{{ my_creds_env_var }}",
        "resource_key": "s3_templated",
    }
    component = S3ResourceComponent(**config)
    assert component.credentials == "{{ my_creds_env_var }}"


@pytest.mark.parametrize(
    "component_class, resource_class",
    [
        (Boto3CredentialsComponent, ResourceWithBoto3Configuration),
        (S3CredentialsComponent, S3Resource),
    ],
)
def test_component_fields_sync_with_resource(component_class, resource_class):
    """Ensure component configuration fields stay in sync with the original resource classes.
    This test fails if a field is added to the Resource but missing in the Component.
    """
    component_fields = set(component_class.model_fields.keys())
    resource_fields = set(resource_class.model_fields.keys())

    assert resource_fields.issubset(component_fields), (
        f"Missing fields in {component_class.__name__}: {resource_fields - component_fields}"
    )
