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
    """Ensures component configuration fields stay in sync with resource classes."""
    component_fields = set(component_class.model_fields.keys())
    resource_fields = set(resource_class.model_fields.keys())
    assert resource_fields.issubset(component_fields)


def test_s3_resource_component_load():
    """Test that S3ResourceComponent correctly instantiates an S3Resource."""
    creds = S3CredentialsComponent(region_name="us-east-1", max_attempts=5)
    component = S3ResourceComponent(credentials=creds, resource_key="my_s3_resource")

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))

    assert defs.resources is not None
    resource = defs.resources["my_s3_resource"]

    assert isinstance(resource, S3Resource)
    assert resource.region_name == "us-east-1"
    assert resource.max_attempts == 5


def test_athena_resource_component_load():
    """Test that AthenaClientResourceComponent correctly instantiates an AthenaClientResource."""
    config = {
        "credentials": {"workgroup": "test_wg", "region_name": "us-east-1"},
        "resource_key": "my_athena",
    }
    component = AthenaClientResourceComponent(**config)
    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))

    assert defs.resources is not None
    resource = defs.resources["my_athena"]
    assert isinstance(resource, AthenaClientResource)
    assert resource.workgroup == "test_wg"


def test_redshift_resource_component_load():
    """Test that RedshiftClientResourceComponent correctly instantiates a RedshiftClientResource."""
    config = {
        "credentials": {"host": "my_host", "user": "admin"},
        "resource_key": "my_redshift",
    }
    component = RedshiftClientResourceComponent(**config)
    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))

    assert defs.resources is not None
    resource = defs.resources["my_redshift"]
    assert isinstance(resource, RedshiftClientResource)
    assert resource.host == "my_host"


def test_ssm_parameter_store_tags_load():
    """Validates that nested ParameterStoreTags can be instantiated."""
    creds = Boto3CredentialsComponent(region_name="us-east-1")

    tags = [ParameterStoreTag(key="Environment", values=["Production"])]
    assert tags[0].key == "Environment"

    component = ParameterStoreResourceComponent(
        credentials=creds, parameters=["/my/param"], resource_key="ps"
    )

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert defs.resources is not None
    resource = defs.resources["ps"]

    assert isinstance(resource, ParameterStoreResource)
    assert resource.parameters == ["/my/param"]


def test_ssm_resource_component_load():
    """Test that SSM components correctly instantiate their resources."""
    creds = Boto3CredentialsComponent(region_name="us-east-1")

    ssm_comp = SSMResourceComponent(credentials=creds, resource_key="ssm")
    ssm_defs = ssm_comp.build_defs(MagicMock(spec=dg.ComponentLoadContext))

    assert ssm_defs.resources is not None
    assert isinstance(ssm_defs.resources["ssm"], SSMResource)

    ps_comp = ParameterStoreResourceComponent(
        credentials=creds, parameters=["/my/param"], resource_key="ps"
    )
    ps_defs = ps_comp.build_defs(MagicMock(spec=dg.ComponentLoadContext))

    assert ps_defs.resources is not None
    resource = ps_defs.resources["ps"]
    assert isinstance(resource, ParameterStoreResource)
    assert resource.parameters == ["/my/param"]


def test_component_no_resource_key():
    """Spec Requirement: Return empty Definitions() if resource_key is not set."""
    creds = Boto3CredentialsComponent(region_name="us-east-1")
    component = SSMResourceComponent(credentials=creds, resource_key=None)

    defs = component.build_defs(MagicMock(spec=dg.ComponentLoadContext))
    assert not defs.resources or len(defs.resources) == 0


def test_credentials_resolution():
    """Test that the component correctly resolves a directly passed Credentials object."""
    raw_config = {"region_name": "eu-central-1"}
    creds = S3CredentialsComponent(**raw_config)

    component = S3ResourceComponent(credentials=creds, resource_key="s3")

    assert isinstance(component.credentials, Boto3CredentialsComponent)
    assert component.credentials.region_name == "eu-central-1"


def test_templated_credentials():
    """Test that the component supports string-based credentials (templates)."""
    component = S3ResourceComponent(credentials="{{ my_template }}", resource_key="s3")
    assert component.credentials == "{{ my_template }}"
