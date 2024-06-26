from dagster._core.definitions.dependency import NodeHandle, NodeInputHandle, NodeOutputHandle


def test_node_input_handle_str():
    assert str(NodeInputHandle(NodeHandle("foo", parent=None), "bar")) == "foo:bar"
    assert (
        str(NodeInputHandle(NodeHandle("foo", parent=NodeHandle("baz", parent=None)), "bar"))
        == "baz.foo:bar"
    )


def test_node_output_handle_str():
    assert str(NodeOutputHandle(NodeHandle("foo", parent=None), "bar")) == "foo:bar"
    assert (
        str(NodeOutputHandle(NodeHandle("foo", parent=NodeHandle("baz", parent=None)), "bar"))
        == "baz.foo:bar"
    )
