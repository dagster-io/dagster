from typing import Dict

import pytest
from dagster import ConfigMapping, DagsterInvalidDefinitionError, execute_pipeline, resource, solid
from dagster.core.definitions.decorators.graph import graph
from dagster.core.definitions.graph import GraphDefinition
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
    result = execute_pipeline(my_job)
    assert result.success


def test_config_mapping_val():
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
        config_mapping={
            "solids": {"do_stuff": {"config": {"msg": "i am here"}}},
            "resources": {"date": {"config": "6/3"}},
        },
    )

    result = execute_pipeline(job)
    assert result.success
    assert result.result_for_solid("do_stuff").output_value() == "i am here on 6/3"


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
        config_mapping=ConfigMapping(
            config_schema={"date": str},  # top level has to be dict
            config_fn=_mapped,
        ),
    )

    result = execute_pipeline(job, run_config={"date": "6/4"})
    assert result.success
    assert result.result_for_solid("do_stuff").output_value() == "i am here on 6/4"


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
        default_config={
            "solids": {"do_stuff": {"config": {"msg": "i am here"}}},
            "resources": {"date": {"config": "6/3"}},
        },
    )

    result = execute_pipeline(job)
    assert result.success
    assert result.result_for_solid("do_stuff").output_value() == "i am here on 6/3"


def test_default_config_with_mapping_fn():
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
        config_mapping=ConfigMapping(
            config_schema={"date": str},  # top level has to be dict
            config_fn=_mapped,
        ),
        default_config={"date": "6/4"},
    )

    result = execute_pipeline(job)
    assert result.success
    assert result.result_for_solid("do_stuff").output_value() == "i am here on 6/4"


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

    def config_fn(date_str: str):
        return {"solids": {"my_solid": {"config": {"date": date_str}}}}

    def partition_fn():
        return ["2020-02-25", "2020-02-26"]

    job = my_graph.to_job(config_mapping=ConfigMapping(config_fn), partitions=partition_fn)
    mode = job.mode_definitions[0]
    partition_set = mode.get_partition_set_def("my_graph")
    partitions = partition_set.get_partitions()
    assert len(partitions) == 2
    assert partitions[0].value == "2020-02-25"
    assert partitions[0].name == "2020-02-25"
    assert partition_set.run_config_for_partition(partitions[0]) == "2020-02-25"


def test_non_str_partitions():
    @solid(config_schema={"date": str})
    def my_solid(_):
        pass

    @graph
    def my_graph():
        my_solid()

    def config_fn(date_blob: Dict[str, str]):
        return {"solids": {"my_solid": {"config": {"date": date_blob["date"]}}}}

    def partition_fn():
        return [{"date": "2020-02-25"}, {"date": "2020-02-26"}]

    job = my_graph.to_job(config_mapping=ConfigMapping(config_fn), partitions=partition_fn)
    mode = job.mode_definitions[0]
    partition_set = mode.get_partition_set_def("my_graph")
    partitions = partition_set.get_partitions()
    assert len(partitions) == 2
    assert partitions[0].value == {"date": "2020-02-25"}
    assert partitions[0].name == str({"date": "2020-02-25"})
    assert partition_set.run_config_for_partition(partitions[0]) == {"date": "2020-02-25"}


def test_partitions_and_default_config():
    @solid(config_schema={"date": str})
    def my_solid(_):
        pass

    @graph
    def my_graph():
        my_solid()

    def partition_fn():
        return []

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="A job can have default_config or partitions, but not both",
    ):
        my_graph.to_job(
            partitions=partition_fn,
            default_config={"solids": {"my_solid": {"config": {"date": "abc"}}}},
        )


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

    result = execute_pipeline(job)
    assert result.success
