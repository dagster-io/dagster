import pytest
from dagster import ConfigMapping, Field, graph, op
from dagster._check import CheckError
from dagster._config import ConfigAnyInstance


def test_op_field_backcompat():
    @op
    def op_without_schema(_):
        pass

    field = op_without_schema.config_schema.as_field()
    assert field.config_type == ConfigAnyInstance
    assert not field.is_required

    @op(config_schema=Field(str))
    def op_with_schema(_):
        pass

    assert op_with_schema.config_schema.is_required is True
    assert op_with_schema.config_schema.default_provided is False
    assert op_with_schema.config_schema.description is None

    with pytest.raises(CheckError):
        op_with_schema.config_schema.default_value  # noqa: B018

    with pytest.raises(CheckError):
        op_with_schema.config_schema.default_value_as_json_str  # noqa: B018

    @op(config_schema=Field(int, default_value=4, description="foo"))
    def op_with_all_properties(_):
        pass

    assert op_with_all_properties.config_schema.is_required is False
    assert op_with_all_properties.config_schema.default_provided is True
    assert op_with_all_properties.config_schema.default_value == 4
    assert op_with_all_properties.config_schema.default_value_as_json_str == "4"
    assert op_with_all_properties.config_schema.description == "foo"


def test_composite_field_backwards_compat():
    @op
    def noop(_):
        pass

    @graph
    def bare_graph():
        noop()

    assert bare_graph.config_schema is None

    @graph(config=ConfigMapping(config_schema=int, config_fn=lambda _: 4))
    def graph_with_int():
        noop()

    assert graph_with_int.config_schema
    assert graph_with_int.config_schema.is_required is True
    assert graph_with_int.config_schema.default_provided is False

    with pytest.raises(CheckError):
        graph_with_int.config_schema.default_value  # noqa: B018

    with pytest.raises(CheckError):
        graph_with_int.config_schema.default_value_as_json_str  # noqa: B018

    @graph(
        config=ConfigMapping(
            config_schema=Field(int, default_value=2, description="bar"),
            config_fn=lambda _: 4,
        )
    )
    def graph_kitchen_sink():
        noop()

    assert graph_kitchen_sink.config_schema
    assert graph_kitchen_sink.config_schema.is_required is False
    assert graph_kitchen_sink.config_schema.default_provided is True
    assert graph_kitchen_sink.config_schema.default_value == 2
    assert graph_kitchen_sink.config_schema.default_value_as_json_str == "2"
    assert graph_kitchen_sink.config_schema.description == "bar"
