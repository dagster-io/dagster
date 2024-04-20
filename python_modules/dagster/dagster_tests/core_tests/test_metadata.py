from dagster import GraphDefinition, IntMetadataValue, NodeInvocation, UrlMetadataValue, op


def test_op_instance_tags():
    called = {}

    @op(tags={"foo": "bar", "baz": "quux"})
    def metadata_op(context):
        assert context.op.tags == {"foo": "oof", "baz": "quux", "bip": "bop"}
        called["yup"] = True

    job_def = GraphDefinition(
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

    result = job_def.execute_in_process()

    assert result.success
    assert called["yup"]


def test_int_metadata_value():
    assert IntMetadataValue(5).value == 5
    assert IntMetadataValue(value=5).value == 5


def test_url_metadata_value():
    url = "http://dagster.io"
    assert UrlMetadataValue(url).value == url
    assert UrlMetadataValue(url).url == url
    assert UrlMetadataValue(url=url).value == url
