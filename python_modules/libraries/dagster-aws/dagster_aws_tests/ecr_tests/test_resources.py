from dagster import op
from dagster._utils.test import wrap_op_in_graph_and_execute

from dagster_aws.ecr import FakeECRPublicResource, fake_ecr_public_resource


def test_ecr_public_get_login_password() -> None:
    @op(required_resource_keys={"ecr_public"})
    def ecr_public_op(context):
        return context.resources.ecr_public.get_login_password()

    result = wrap_op_in_graph_and_execute(
        ecr_public_op,
        resources={"ecr_public": fake_ecr_public_resource},
    )

    assert result.output_value() == "token"


def test_ecr_public_get_login_password_pythonic() -> None:
    @op
    def ecr_public_op(ecr_public: FakeECRPublicResource):
        return ecr_public.get_client().get_login_password()

    result = wrap_op_in_graph_and_execute(
        ecr_public_op,
        resources={"ecr_public": FakeECRPublicResource()},
    )

    assert result.output_value() == "token"
