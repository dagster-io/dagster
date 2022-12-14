from dagster import DynamicOutput, Output


def test_output_object_equality():
    def _get_output():
        return Output(5, output_name="foo", metadata={"foo": "bar"})

    assert _get_output() == _get_output()

    assert not _get_output() == Output(6, output_name="foo", metadata={"foo": "bar"})
    assert not _get_output() == Output(5, output_name="diff", metadata={"foo": "bar"})

    assert not _get_output() == Output(5, output_name="foo", metadata={"foo": "baz"})

    assert not _get_output() == DynamicOutput(
        5, output_name="foo", metadata={"foo": "bar"}, mapping_key="blah"
    )


def test_dynamic_output_object_equality():
    def _get_output():
        return DynamicOutput(5, output_name="foo", mapping_key="bar", metadata={"foo": "bar"})

    assert _get_output() == _get_output()

    assert not _get_output() == DynamicOutput(
        6, output_name="foo", metadata={"foo": "bar"}, mapping_key="bar"
    )
    assert not _get_output() == DynamicOutput(
        5, output_name="diff", metadata={"foo": "bar"}, mapping_key="bar"
    )

    assert not _get_output() == DynamicOutput(
        5, output_name="foo", metadata={"foo": "baz"}, mapping_key="bar"
    )
