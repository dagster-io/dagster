from unittest.mock import MagicMock

import dagster as dg

from dagster_aws.components import (
    Boto3CredentialsComponent,
    S3CredentialsComponent,
    S3ResourceComponent,
)
from dagster_aws.s3.resources import S3Resource


def test_s3_resource_component_load():
    config = {
        "credentials": {
            "region_name": "us-east-1",
            "max_attempts": 5,
        },
        "resource_key": "my_s3_resource",
    }

    component = S3ResourceComponent(**config)

    assert isinstance(component._resource, S3Resource)  # noqa: SLF001
    assert component._resource.region_name == "us-east-1"  # noqa: SLF001
    assert component._resource.max_attempts == 5  # noqa: SLF001

    mock_context = MagicMock(spec=dg.ComponentLoadContext)
    mock_context.params = {}

    defs = component.build_defs(mock_context)

    assert defs.resources is not None
    assert defs.resources["my_s3_resource"] is not None


def test_credentials_resolution():
    raw_config = {"region_name": "eu-central-1"}
    creds = S3CredentialsComponent(**raw_config)

    component = S3ResourceComponent(credentials=creds, resource_key="s3")

    assert isinstance(component.credentials, Boto3CredentialsComponent)
    assert component.credentials.region_name == "eu-central-1"


def test_templated_credentials():
    # Simulate a case where credentials come from a template/env var string
    config = {
        "credentials": "{{ my_creds_env_var }}",
        "resource_key": "s3_templated",
    }
    component = S3ResourceComponent(**config)
    assert component.credentials == "{{ my_creds_env_var }}"
