import dagster as dg


def test_output_object_equality():
    def _get_output():
        return dg.Output(5, output_name="foo", metadata={"foo": "bar"}, tags={"baz": "qux"})

    assert _get_output() == _get_output()

    assert not _get_output() == dg.Output(
        6, output_name="foo", metadata={"foo": "bar"}, tags={"baz": "qux"}
    )
    assert not _get_output() == dg.Output(
        5, output_name="diff", metadata={"foo": "bar"}, tags={"baz": "qux"}
    )

    assert not _get_output() == dg.Output(
        5, output_name="foo", metadata={"foo": "baz"}, tags={"baz": "qux"}
    )
    assert not _get_output() == dg.Output(
        5, output_name="foo", metadata={"foo": "bar"}, tags={"baz": "qub"}
    )

    assert not _get_output() == dg.DynamicOutput(
        5, output_name="foo", metadata={"foo": "bar"}, mapping_key="blah"
    )


def test_dynamic_output_object_equality():
    def _get_output():
        return dg.DynamicOutput(5, output_name="foo", mapping_key="bar", metadata={"foo": "bar"})

    assert _get_output() == _get_output()

    assert not _get_output() == dg.DynamicOutput(
        6, output_name="foo", metadata={"foo": "bar"}, mapping_key="bar"
    )
    assert not _get_output() == dg.DynamicOutput(
        5, output_name="diff", metadata={"foo": "bar"}, mapping_key="bar"
    )

    assert not _get_output() == dg.DynamicOutput(
        5, output_name="foo", metadata={"foo": "baz"}, mapping_key="bar"
    )
