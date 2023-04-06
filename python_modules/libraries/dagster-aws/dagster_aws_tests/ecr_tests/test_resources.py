from dagster import op
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_aws.ecr import fake_ecr_public_resource


def test_ecr_public_get_login_password():
    @op(required_resource_keys={"ecr_public"})
    def ecr_public_solid(context):
        return context.resources.ecr_public.get_login_password()

    result = wrap_op_in_graph_and_execute(
        ecr_public_solid,
        resources={"ecr_public": fake_ecr_public_resource},
    )

    assert result.output_value() == "token"
