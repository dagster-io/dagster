from dagster import GraphDefinition, NodeInvocation, op


def test_solid_instance_tags():
    called = {}

    @op(tags={"foo": "bar", "baz": "quux"})
    def metadata_op(context):
        assert context.op.tags == {"foo": "oof", "baz": "quux", "bip": "bop"}
        called["yup"] = True

    pipeline = GraphDefinition(
        name="metadata_pipeline",
        node_defs=[metadata_op],
        dependencies={
            NodeInvocation(
                "metadata_op",
                alias="aliased_metadata_op",
                tags={"foo": "oof", "bip": "bop"},
            ): {}
        },
    ).to_job()

    result = pipeline.execute_in_process()

    assert result.success
    assert called["yup"]
