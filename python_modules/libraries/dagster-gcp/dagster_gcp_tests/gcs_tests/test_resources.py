from dagster import ModeDefinition, execute_solid, solid
from dagster_gcp.gcs.resources import gcs_resource

PROJECT_ID = "test-project1231"


def test_gcs_resource():
    @solid(required_resource_keys={"gcs"})
    def gcs_solid(context):
        assert context.resources.gcs
        assert context.resources.gcs.project == PROJECT_ID

    result = execute_solid(
        gcs_solid,
        run_config={"resources": {"gcs": {"config": {"project": PROJECT_ID}}}},
        mode_def=ModeDefinition(resource_defs={"gcs": gcs_resource}),
    )
    assert result.success
