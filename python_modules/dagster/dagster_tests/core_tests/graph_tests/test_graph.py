import pytest
from dagster import ConfigMapping, graph, logger, op, resource, solid, success_hook
from dagster.core.definitions.graph import GraphDefinition
from dagster.core.definitions.partition import (
    Partition,
    PartitionedConfig,
    StaticPartitionsDefinition,
)
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.execute import execute_in_process


def get_solids():
    @solid
    def emit_one(_):
        return 1

    @solid
    def add(_, x, y):
        return x + y

    return emit_one, add


def test_basic_graph():
    emit_one, add = get_solids()

    @graph
    def get_two():
        return add(emit_one(), emit_one())

    assert isinstance(get_two, GraphDefinition)

    result = execute_in_process(get_two)

    assert result.success

    result = get_two.execute_in_process()
    assert result.success


def test_composite_graph():
    emit_one, add = get_solids()

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

    @solid(required_resource_keys={"a"})
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


def test_config_mapping_fn():
    @resource(config_schema=str)
    def date(context) -> str:
        return context.resource_config

    @solid(
        required_resource_keys={"date"},
        config_schema={"msg": str},
    )
    def do_stuff(context):
        return f"{context.solid_config['msg'] } on {context.resources.date}"

    @graph
    def needs_config():
        do_stuff()

    def _mapped(val):
        return {
            "solids": {"do_stuff": {"config": {"msg": "i am here"}}},
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

    @solid(
        required_resource_keys={"date"},
        config_schema={"msg": str},
    )
    def do_stuff(context):
        return f"{context.solid_config['msg'] } on {context.resources.date}"

    @graph
    def needs_config():
        do_stuff()

    job = needs_config.to_job(
        resource_defs={"date": date},
        config={
            "solids": {"do_stuff": {"config": {"msg": "i am here"}}},
            "resources": {"date": {"config": "6/3"}},
        },
    )

    result = job.execute_in_process()
    assert result.success
    assert result.result_for_node("do_stuff").output_values["result"] == "i am here on 6/3"


def test_suffix():
    emit_one, add = get_solids()

    @graph
    def get_two():
        return add(emit_one(), emit_one())

    assert isinstance(get_two, GraphDefinition)

    my_job = get_two.to_job(name="get_two_prod")
    assert my_job.name == "get_two_prod"


def test_partitions():
    @solid(config_schema={"date": str})
    def my_solid(_):
        pass

    @graph
    def my_graph():
        my_solid()

    def config_fn(partition: Partition):
        return {"solids": {"my_solid": {"config": {"date": partition.value}}}}

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
        "solids": {"my_solid": {"config": {"date": "2020-02-25"}}}
    }


def test_tags_on_job():
    @solid
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


def test_logger_defs():
    @solid
    def my_solid(_):
        pass

    @graph
    def my_graph():
        my_solid()

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

    @solid
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
