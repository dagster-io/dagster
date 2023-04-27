import inspect
from typing import Type
import pytest
from dagster import SensorDefinition, graph
from dagster._core.errors import DagsterInvalidDefinitionError


def test_jobs_attr() -> None:
    def eval_fn() -> None:
        pass

    @graph
    def my_graph() -> None:
        pass

    sensor = SensorDefinition(evaluation_fn=eval_fn, job=my_graph)
    assert sensor.job.name == my_graph.name

    sensor = SensorDefinition(evaluation_fn=eval_fn, job_name="my_pipeline")
    with pytest.raises(
        DagsterInvalidDefinitionError, match="No job was provided to SensorDefinition."
    ):
        sensor.job

    @graph
    def my_second_graph() -> None:
        pass

    sensor = SensorDefinition(evaluation_fn=eval_fn, jobs=[my_graph, my_second_graph])
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Job property not available when SensorDefinition has multiple jobs.",
    ):
        sensor.job


def test_direct_sensor_definition_instantiation() -> None:
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Must provide evaluation_fn to SensorDefinition.",
    ):
        SensorDefinition()


def assert_internal_init_class_follow_rules(cls: Type):
    internal_init_argspec = inspect.getfullargspec(cls.internal_init)
    init_args_spec = inspect.getfullargspec(cls.__init__)

    # internal_init cannot have default
    assert internal_init_argspec.defaults is None
    # internal_init can only have kwonlyargs
    assert internal_init_argspec.args == []

    assert internal_init_argspec.kwonlyargs == (
        init_args_spec.args[1:] + init_args_spec.kwonlyargs  # exclude self
    )


def test_internal_init_matches() -> None:
    assert_internal_init_class_follow_rules(SensorDefinition)
