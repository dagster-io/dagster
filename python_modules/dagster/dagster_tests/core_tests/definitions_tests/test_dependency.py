from dagster._core.definitions.dependency import NodeHandle, NodeInputHandle, NodeOutputHandle


def test_node_input_handle_str():
    assert (
        str(NodeInputHandle(node_handle=NodeHandle("foo", parent=None), input_name="bar"))
        == "foo:bar"
    )
    assert (
        str(
            NodeInputHandle(
                node_handle=NodeHandle("foo", parent=NodeHandle("baz", parent=None)),
                input_name="bar",
            )
        )
        == "baz.foo:bar"
    )


def test_node_output_handle_str():
    assert (
        str(NodeOutputHandle(node_handle=NodeHandle("foo", parent=None), output_name="bar"))
        == "foo:bar"
    )
    assert (
        str(
            NodeOutputHandle(
                node_handle=NodeHandle("foo", parent=NodeHandle("baz", parent=None)),
                output_name="bar",
            )
        )
        == "baz.foo:bar"
    )
