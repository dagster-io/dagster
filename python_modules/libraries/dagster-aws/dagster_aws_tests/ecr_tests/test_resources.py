import pytest
from dagster import op
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_aws.ecr import FakeECRPublicResource, fake_ecr_public_resource


@pytest.fixture(name="ecr_public_resource", params=[True, False])
def ecr_public_resource_fixture(request) -> ResourceDefinition:
    if request.param:
        return fake_ecr_public_resource
    else:
        return FakeECRPublicResource.configure_at_launch()


def test_ecr_public_get_login_password(ecr_public_resource):
    @op(required_resource_keys={"ecr_public"})
    def ecr_public_solid(context):
        return context.resources.ecr_public.get_login_password()

    result = wrap_op_in_graph_and_execute(
        ecr_public_solid,
        resources={"ecr_public": fake_ecr_public_resource},
    )

    assert result.output_value() == "token"
