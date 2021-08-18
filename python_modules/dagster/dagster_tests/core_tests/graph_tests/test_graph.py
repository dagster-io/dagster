import enum
import json

import pytest
from dagster import (
    ConfigMapping,
    Enum,
    Field,
    Permissive,
    Shape,
    graph,
    logger,
    op,
    resource,
    success_hook,
)
from dagster.check import CheckError
from dagster.core.definitions.graph import GraphDefinition
from dagster.core.definitions.partition import (
    Partition,
    PartitionedConfig,
    StaticPartitionsDefinition,
)
from dagster.core.errors import DagsterInvalidConfigError, DagsterInvalidDefinitionError
from dagster.core.execution.execute import execute_in_process


def get_ops():
    @op
    def emit_one(_):
        return 1

    @op
    def add(_, x, y):
        return x + y

    return emit_one, add


def test_basic_graph():
    emit_one, add = get_ops()

    @graph
    def get_two():
        return add(emit_one(), emit_one())

    assert isinstance(get_two, GraphDefinition)

    result = execute_in_process(get_two)

    assert result.success

    result = get_two.execute_in_process()
    assert result.success


def test_aliased_graph():
    emit_one, add = get_ops()

    @graph
    def get_two():
        return add(emit_one(), emit_one.alias("emit_one_part_two")())

    assert isinstance(get_two, GraphDefinition)

    result = execute_in_process(get_two)

    assert result.success

    result_for_non_aliased = result.result_for_node("emit_one")
    assert result_for_non_aliased.output_values["result"] == 1
    result_for_aliased = result.result_for_node("emit_one_part_two")
    assert result_for_aliased.output_values["result"] == 1

    result = get_two.execute_in_process()
    assert result.success


def test_composite_graph():
    emit_one, add = get_ops()

    @graph
    def add_one(x):
        return add(emit_one(), x)

    @graph
    def add_two(x):
        return add(add_one(x), emit_one())

    assert isinstance(add_two, GraphDefinition)


def test_with_resources():
    @resource
    def a_resource(_):
        return "a"

    @op(required_resource_keys={"a"})
    def needs_resource(context):
        return context.resources.a

    @graph
    def my_graph():
        needs_resource()

    # proxy for "executable/job"
    my_job = my_graph.to_job(resource_defs={"a": a_resource})
    assert my_job.name == "my_graph"
    result = my_job.execute_in_process()
    assert result.success

    result = my_graph.execute_in_process(resources={"a": "foo"})
    assert result.success


def test_error_on_invalid_resource_key():
    @resource
    def test_resource():
        return "test-resource"

    @op(required_resource_keys={"test-resource"})
    def needs_resource(_):
        return ""

    @graph
    def test_graph():
        needs_resource()

    with pytest.raises(CheckError, match="test-resource"):
        test_graph.to_job(
            resource_defs={
                "test-resource": test_resource,
            }
        )


def test_config_mapping_fn():
    @resource(config_schema=str)
    def date(context) -> str:
        return context.resource_config

    @op(
        required_resource_keys={"date"},
        config_schema={"msg": str},
    )
    def do_stuff(context):
        return f"{context.op_config['msg'] } on {context.resources.date}"

    @graph
    def needs_config():
        do_stuff()

    def _mapped(val):
        return {
            "ops": {"do_stuff": {"config": {"msg": "i am here"}}},
            "resources": {"date": {"config": val["date"]}},
        }

    job = needs_config.to_job(
        resource_defs={"date": date},
        config=ConfigMapping(
            config_schema={"date": str},  # top level has to be dict
            config_fn=_mapped,
        ),
    )

    result = job.execute_in_process(run_config={"date": "6/4"})
    assert result.success
    assert result.result_for_node("do_stuff").output_values["result"] == "i am here on 6/4"


def test_default_config():
    @resource(config_schema=str)
    def date(context) -> str:
        return context.resource_config

    @op(
        required_resource_keys={"date"},
        config_schema={"msg": str},
    )
    def do_stuff(context):
        return f"{context.op_config['msg'] } on {context.resources.date}"

    @graph
    def needs_config():
        do_stuff()

    job = needs_config.to_job(
        resource_defs={"date": date},
        config={
            "ops": {"do_stuff": {"config": {"msg": "i am here"}}},
            "resources": {"date": {"config": "6/3"}},
        },
    )

    result = job.execute_in_process()
    assert result.success
    assert result.result_for_node("do_stuff").output_values["result"] == "i am here on 6/3"


def test_suffix():
    emit_one, add = get_ops()

    @graph
    def get_two():
        return add(emit_one(), emit_one())

    assert isinstance(get_two, GraphDefinition)

    my_job = get_two.to_job(name="get_two_prod")
    assert my_job.name == "get_two_prod"


def test_partitions():
    @op(config_schema={"date": str})
    def my_op(_):
        pass

    @graph
    def my_graph():
        my_op()

    def config_fn(partition: Partition):
        return {"ops": {"my_op": {"config": {"date": partition.value}}}}

    job = my_graph.to_job(
        config=PartitionedConfig(
            run_config_for_partition_fn=config_fn,
            partitions_def=StaticPartitionsDefinition(
                [Partition("2020-02-25"), Partition("2020-02-26")]
            ),
        ),
    )
    mode = job.mode_definitions[0]
    partition_set = mode.get_partition_set_def("my_graph")
    partitions = partition_set.get_partitions()
    assert len(partitions) == 2
    assert partitions[0].value == "2020-02-25"
    assert partitions[0].name == "2020-02-25"
    assert partition_set.run_config_for_partition(partitions[0]) == {
        "ops": {"my_op": {"config": {"date": "2020-02-25"}}}
    }


def test_tags_on_job():
    @op
    def basic():
        pass

    @graph
    def basic_graph():
        basic()

    tags = {"my_tag": "yes"}
    job = basic_graph.to_job(tags=tags)
    assert job.tags == tags

    result = job.execute_in_process()
    assert result.success


def test_non_string_tag():
    @op
    def basic():
        pass

    @graph
    def basic_graph():
        basic()

    inner = {"a": "b"}
    tags = {"my_tag": inner}
    job = basic_graph.to_job(tags=tags)
    assert job.tags == {"my_tag": json.dumps(inner)}

    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid value for tag"):
        basic_graph.to_job(tags={"my_tag": basic_graph})


def test_logger_defs():
    @op
    def my_op(_):
        pass

    @graph
    def my_graph():
        my_op()

    @logger
    def my_logger(_):
        pass

    my_job = my_graph.to_job(logger_defs={"abc": my_logger})
    assert my_job.mode_definitions[0].loggers == {"abc": my_logger}


def test_job_with_hooks():
    entered = []

    @success_hook
    def basic_hook(_):
        entered.append("yes")

    @op
    def basic_emit():
        pass

    @graph
    def basic_hook_graph():
        basic_emit()

    job_for_hook_testing = basic_hook_graph.to_job(hooks={basic_hook})

    result = job_for_hook_testing.execute_in_process()

    assert result.success
    assert entered == ["yes"]


def test_composition_bug():
    @op
    def expensive_task1():
        pass

    @op
    def expensive_task2(_my_input):
        pass

    @op
    def expensive_task3(_my_input):
        pass

    @graph
    def my_graph1():
        task1_done = expensive_task1()
        _task2_done = expensive_task2(task1_done)

    @graph
    def my_graph2():
        _task3_done = expensive_task3()

    @graph
    def my_graph_final():
        my_graph1()
        my_graph2()

    my_job = my_graph_final.to_job()

    index = my_job.get_pipeline_index()
    assert index.get_node_def_snap("my_graph1")
    assert index.get_node_def_snap("my_graph2")


def test_conflict():
    @op(name="conflict")
    def test_1():
        pass

    @graph(name="conflict")
    def test_2():
        pass

    with pytest.raises(DagsterInvalidDefinitionError, match="definitions with the same name"):

        @graph
        def _conflict_zone():
            test_1()
            test_2()


def test_desc():
    @graph(description="graph desc")
    def empty():
        pass

    job = empty.to_job()
    # should we inherit from the graph instead?
    assert job.description == None

    desc = "job desc"
    job = empty.to_job(description=desc)
    assert job.description == desc


def test_config_naming_collisions():
    @op(config_schema={"solids": Permissive(), "ops": Permissive()})
    def my_op(context):
        return context.op_config

    @graph
    def my_graph():
        return my_op()

    config = {
        "solids": {"solids": {"foo": {"config": {"foobar": "bar"}}}},
        "ops": {"solids": {"foo": {"config": {"foobar": "bar"}}}},
    }
    result = my_graph.execute_in_process(
        run_config={"ops": {"my_graph": {"ops": {"my_op": {"config": config}}}}}
    )
    assert result.success
    assert result.output_values["result"] == config

    @graph
    def solids():
        return my_op()

    result = solids.execute_in_process(
        run_config={"ops": {"solids": {"ops": {"my_op": {"config": config}}}}}
    )
    assert result.success
    assert result.output_values["result"] == config


def test_to_job_default_config_field_aliasing():
    @op
    def add_one(x):
        return x + 1

    @graph
    def my_graph():
        return add_one()

    my_job = my_graph.to_job(config={"ops": {"add_one": {"inputs": {"x": {"value": 1}}}}})

    result = my_job.execute_in_process()
    assert result.success

    result = my_job.execute_in_process({"solids": {"add_one": {"inputs": {"x": {"value": 1}}}}})
    assert result.success

    result = my_job.execute_in_process({"ops": {"add_one": {"inputs": {"x": {"value": 1}}}}})
    assert result.success


def test_to_job_incomplete_default_config():
    @op(config_schema={"foo": str})
    def my_op(_):
        pass

    @graph
    def my_graph():
        my_op()

    default_config_error = "Error in config when building job 'my_job' from graph 'my_graph' "
    invalid_default_error = "Invalid default_value for Field."
    invalid_configs = [
        (
            {},
            default_config_error,
        ),  # Not providing required config nested into the op config schema.
        (
            {"ops": {"my_op": {"config": {"foo": "bar"}}, "not_my_op": {"config": {"foo": "bar"}}}},
            invalid_default_error,
        ),  # Providing extraneous config for an op that doesn't exist.
        (
            {
                "ops": {"my_op": {"config": {"foo": "bar"}}},
                "solids": {"my_op": {"config": {"foo": "bar"}}},
            },
            default_config_error,
        ),  # Providing the same config with multiple aliases.
    ]
    # Ensure that errors nested into the config tree are caught
    for invalid_config, error_msg in invalid_configs:
        with pytest.raises(
            DagsterInvalidConfigError,
            match=error_msg,
        ):
            my_graph.to_job(name="my_job", config=invalid_config)


class TestEnum(enum.Enum):
    ONE = 1
    TWO = 2


def test_enum_config_mapping():
    @op(
        config_schema={
            "my_enum": Field(
                Enum.from_python_enum(TestEnum), is_required=False, default_value="ONE"
            )
        }
    )
    def my_op(context):
        return context.op_config["my_enum"]

    @graph
    def my_graph():
        my_op()

    def _use_defaults_mapping(_):
        return {}

    use_defaults = my_graph.to_job(config=ConfigMapping(config_fn=_use_defaults_mapping))
    result = use_defaults.execute_in_process()
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == TestEnum.ONE

    def _override_defaults_mapping(_):
        return {"ops": {"my_op": {"config": {"my_enum": "TWO"}}}}

    override_defaults = my_graph.to_job(config=ConfigMapping(config_fn=_override_defaults_mapping))
    result = override_defaults.execute_in_process()
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == TestEnum.TWO

    def _ingest_config_mapping(x):
        return {"ops": {"my_op": {"config": {"my_enum": x["my_field"]}}}}

    default_config_mapping = ConfigMapping(
        config_fn=_ingest_config_mapping,
        config_schema=Shape(
            {
                "my_field": Field(
                    Enum.from_python_enum(TestEnum), is_required=False, default_value="TWO"
                )
            }
        ),
        receive_processed_config_values=False,
    )
    ingest_mapping = my_graph.to_job(config=default_config_mapping)
    result = ingest_mapping.execute_in_process()
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == TestEnum.TWO

    no_default_config_mapping = ConfigMapping(
        config_fn=_ingest_config_mapping,
        config_schema=Shape({"my_field": Field(Enum.from_python_enum(TestEnum), is_required=True)}),
        receive_processed_config_values=False,
    )
    ingest_mapping_no_default = my_graph.to_job(config=no_default_config_mapping)
    result = ingest_mapping_no_default.execute_in_process(run_config={"my_field": "TWO"})
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == TestEnum.TWO

    def _ingest_post_processed_config(x):
        assert x["my_field"] == TestEnum.TWO
        return {"ops": {"my_op": {"config": {"my_enum": "TWO"}}}}

    config_mapping_with_preprocessing = ConfigMapping(
        config_fn=_ingest_post_processed_config,
        config_schema=Shape({"my_field": Field(Enum.from_python_enum(TestEnum), is_required=True)}),
    )
    ingest_preprocessing = my_graph.to_job(config=config_mapping_with_preprocessing)
    result = ingest_preprocessing.execute_in_process(run_config={"my_field": "TWO"})
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == TestEnum.TWO


def test_enum_default_config():
    @op(
        config_schema={
            "my_enum": Field(
                Enum.from_python_enum(TestEnum), is_required=False, default_value="ONE"
            )
        }
    )
    def my_op(context):
        return context.op_config["my_enum"]

    @graph
    def my_graph():
        my_op()

    my_job = my_graph.to_job(config={"ops": {"my_op": {"config": {"my_enum": "TWO"}}}})
    result = my_job.execute_in_process()
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == TestEnum.TWO


def test_enum_to_execution():
    @op(
        config_schema={
            "my_enum": Field(
                Enum.from_python_enum(TestEnum), is_required=False, default_value="ONE"
            )
        }
    )
    def my_op(context):
        return context.op_config["my_enum"]

    @graph
    def my_graph():
        my_op()

    my_job = my_graph.to_job()
    result = my_job.execute_in_process()
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == TestEnum.ONE

    result = my_graph.execute_in_process(
        {"ops": {"my_graph": {"ops": {"my_op": {"config": {"my_enum": "TWO"}}}}}}
    )
    assert result.success
    assert result.result_for_node("my_op").output_values["result"] == TestEnum.TWO
