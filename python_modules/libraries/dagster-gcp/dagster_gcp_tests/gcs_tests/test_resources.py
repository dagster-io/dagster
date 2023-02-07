from dagster import build_op_context, op
from dagster_gcp.gcs.resources import gcs_resource

PROJECT_ID = "test-project1231"


def test_gcs_resource():
    @op(required_resource_keys={"gcs"})
    def gcs_op(context):
        assert context.resources.gcs
        assert context.resources.gcs.project == PROJECT_ID
        return 1

    context = build_op_context(resources={"gcs": gcs_resource.configured({"project": PROJECT_ID})})

    assert gcs_op(context)
