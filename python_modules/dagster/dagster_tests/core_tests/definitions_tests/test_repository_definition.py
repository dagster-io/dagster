import datetime
from collections import defaultdict

import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    PipelineDefinition,
    SolidDefinition,
    daily_schedule,
    lambda_solid,
    repository,
)


def create_single_node_pipeline(name, called):
    called[name] = called[name] + 1
    return PipelineDefinition(
        name=name,
        solid_defs=[
            SolidDefinition(
                name=name + "_solid",
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args, **_kwargs: None,
            )
        ],
    )


def test_repo_lazy_definition():
    called = defaultdict(int)

    @repository
    def lazy_repo():
        return {
            "pipelines": {
                "foo": lambda: create_single_node_pipeline("foo", called),
                "bar": lambda: create_single_node_pipeline("bar", called),
            }
        }

    foo_pipeline = lazy_repo.get_pipeline("foo")
    assert isinstance(foo_pipeline, PipelineDefinition)
    assert foo_pipeline.name == "foo"

    assert "foo" in called
    assert called["foo"] == 1
    assert "bar" not in called

    bar_pipeline = lazy_repo.get_pipeline("bar")
    assert isinstance(bar_pipeline, PipelineDefinition)
    assert bar_pipeline.name == "bar"

    assert "foo" in called
    assert called["foo"] == 1
    assert "bar" in called
    assert called["bar"] == 1

    foo_pipeline = lazy_repo.get_pipeline("foo")
    assert isinstance(foo_pipeline, PipelineDefinition)
    assert foo_pipeline.name == "foo"

    assert "foo" in called
    assert called["foo"] == 1

    pipelines = lazy_repo.get_all_pipelines()

    assert set(["foo", "bar"]) == {pipeline.name for pipeline in pipelines}

    assert lazy_repo.solid_def_named("foo_solid").name == "foo_solid"
    assert lazy_repo.solid_def_named("bar_solid").name == "bar_solid"


def test_dupe_solid_repo_definition():
    @lambda_solid(name="same")
    def noop():
        pass

    @lambda_solid(name="same")
    def noop2():
        pass

    @repository
    def error_repo():
        return {
            "pipelines": {
                "first": lambda: PipelineDefinition(name="first", solid_defs=[noop]),
                "second": lambda: PipelineDefinition(name="second", solid_defs=[noop2]),
            }
        }

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        error_repo.get_all_pipelines()

    assert str(exc_info.value) == (
        "Duplicate solids found in repository with name 'same'. Solid definition names must be "
        "unique within a repository. Solid is defined in pipeline 'first' and in pipeline "
        "'second'."
    )


def test_non_lazy_pipeline_dict():
    called = defaultdict(int)

    @repository
    def some_repo():
        return [
            create_single_node_pipeline("foo", called),
            create_single_node_pipeline("bar", called),
        ]

    assert some_repo.get_pipeline("foo").name == "foo"
    assert some_repo.get_pipeline("bar").name == "bar"


def test_conflict():
    called = defaultdict(int)
    with pytest.raises(Exception, match="Duplicate pipeline definition found for pipeline foo"):

        @repository
        def _some_repo():
            return [
                create_single_node_pipeline("foo", called),
                create_single_node_pipeline("foo", called),
            ]


def test_key_mismatch():
    called = defaultdict(int)

    @repository
    def some_repo():
        return {"pipelines": {"foo": lambda: create_single_node_pipeline("bar", called)}}

    with pytest.raises(Exception, match="name in PipelineDefinition does not match"):
        some_repo.get_pipeline("foo")


def test_non_pipeline_in_pipelines():
    with pytest.raises(DagsterInvalidDefinitionError, match="all elements of list must be of type"):

        @repository
        def _some_repo():
            return ["not-a-pipeline"]


def test_schedule_partitions():
    @daily_schedule(
        pipeline_name="foo",
        start_date=datetime.datetime(2020, 1, 1),
    )
    def daily_foo(_date):
        return {}

    @repository
    def some_repo():
        return {
            "pipelines": {"foo": lambda: create_single_node_pipeline("foo", {})},
            "schedules": {"daily_foo": lambda: daily_foo},
        }

    assert len(some_repo.schedule_defs) == 1
    assert len(some_repo.partition_set_defs) == 1
    assert some_repo.get_partition_set_def("daily_foo_partitions")
