from dagster import op, NodeInvocation
from dagster._legacy import PipelineDefinition, execute_pipeline, solid


def test_solid_instance_tags():
    called = {}

    @op(tags={"foo": "bar", "baz": "quux"})
    def metadata_op(context):
        assert context.op.tags == {"foo": "oof", "baz": "quux", "bip": "bop"}
        called["yup"] = True

    pipeline = PipelineDefinition(
        name="metadata_pipeline",
        solid_defs=[metadata_op],
        dependencies={
            NodeInvocation(
                "metadata_op",
                alias="aliased_metadata_op",
                tags={"foo": "oof", "bip": "bop"},
            ): {}
        },
    )

    result = execute_pipeline(
        pipeline,
    )

    assert result.success
    assert called["yup"]
