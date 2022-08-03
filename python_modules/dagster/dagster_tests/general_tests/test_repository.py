"""
Repository of test pipelines
"""

import pytest

from dagster import (
    GraphDefinition,
    Int,
    JobDefinition,
    graph,
    job,
    multiprocess_executor,
    op,
    repository,
    resource,
)
from dagster._check import CheckError


def define_empty_job():
    return JobDefinition(name="empty_job", graph_def=GraphDefinition(name="empty_graph"))


def define_simple_job():
    @op
    def return_two():
        return 2

    @job
    def simple_job():
        return_two()

    return simple_job


def define_with_resources_job():
    @resource(config_schema=Int)
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @resource(config_schema=Int)
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @resource(config_schema={"num_one": Int, "num_two": Int})
    def double_adder_resource(init_context):
        return (
            lambda x: x
            + init_context.resource_config["num_one"]
            + init_context.resource_config["num_two"]
        )

    @op(required_resource_keys={"modifier"})
    def apply_to_three(context):
        return context.resources.modifier(3)

    @graph
    def my_graph():
        apply_to_three()

    adder_job = my_graph.to_job(name="adder_job", resource_defs={"modifier": adder_resource})
    multer_job = my_graph.to_job(name="multer_job", resource_defs={"modifier": multer_resource})
    double_adder_job = my_graph.to_job(
        name="double_adder_job", resource_defs={"modifier": double_adder_resource}
    )
    multi_job = my_graph.to_job(
        "multi_job", resource_defs={"modifier": adder_resource}, executor_def=multiprocess_executor
    )

    return [adder_job, multer_job, double_adder_job, multi_job]


@repository
def dagster_test_repository():
    return [
        define_empty_job(),
        define_simple_job(),
        *define_with_resources_job(),
    ]


def test_repository_construction():
    assert dagster_test_repository


@repository
def empty_repository():
    return []


def test_invalid_repository():
    with pytest.raises(CheckError):

        @repository
        def invalid_repository(_invalid_arg: str):
            return []
