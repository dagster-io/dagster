import enum
import re

import pytest
from dagster import DagsterInvalidConfigError, Enum, Field, check, config_mapping, graph, op

def test_empty_config_mapping():
    @op
    def empty_op():
        pass

    @graph
    def empty_graph():
        empty_op()

    @config_mapping
    def empty_config_mapping(_):
        return {}

    assert empty_graph.to_job(config=empty_config_mapping).execute_in_process().success

@op
def my_op(context):
    return context.op_config["foo"]

@graph
def my_graph():
    my_op()

def test_bare_config_mapping():
    @config_mapping
    def my_config_mapping(val):
        return {"ops": {"my_op": {"config": {"foo": val["foo"]}}}}

    result = my_graph.to_job(config=my_config_mapping).execute_in_process(run_config={"foo": "bar"})
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == "bar"

def test_no_params_config_mapping():
    @config_mapping()
    def my_config_mapping(val):
        return {"ops": {"my_op": {"config": {"foo": val["foo"]}}}}

    result = my_graph.to_job(config=my_config_mapping).execute_in_process(run_config={"foo": "bar"})
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == "bar"

def test_conf_schema_typing_config_mapping():
    @config_mapping(config_schema={"foo": str})
    def my_config_mapping(val):
        return {"ops": {"my_op": {"config": {"foo": val["foo"]}}}}

    with pytest.raises(DagsterInvalidConfigError):
        my_graph.to_job(config=my_config_mapping).execute_in_process(run_config={"foo": 1})
        
    with pytest.raises(DagsterInvalidConfigError):
        my_graph.to_job(config=my_config_mapping).execute_in_process()

    result = my_graph.to_job(config=my_config_mapping).execute_in_process(run_config={"foo": "bar"})
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == "bar"

def test_receive_processed_config_values():
    class TestEnum(enum.Enum):
        FOO = 1
        BAR = 2
    
    enum_conf_schema = {
                "foo": Field(
                    Enum.from_python_enum(TestEnum), is_required=False, default_value="BAR"
                )
            }
    
    @config_mapping(config_schema=enum_conf_schema)
    def processed_config_mapping(outer_config):
        return {"ops": {"my_op": {"config": {"foo": outer_config["foo"]}}}}

    processed_result = my_graph.to_job(config=processed_config_mapping).execute_in_process()
    assert processed_result.success
    assert processed_result.result_for_node("my_op").output_values["result"] == TestEnum.BAR

    @config_mapping(config_schema=enum_conf_schema, receive_processed_config_values=False)
    def unprocessed_config_mapping(outer_config):
        return {"ops": {"my_op": {"config": {"foo": outer_config["foo"]}}}}

    unprocessed_result = my_graph.to_job(config=unprocessed_config_mapping).execute_in_process()
    assert unprocessed_result.success
    assert unprocessed_result.result_for_node("my_op").output_values["result"] == "BAR"
