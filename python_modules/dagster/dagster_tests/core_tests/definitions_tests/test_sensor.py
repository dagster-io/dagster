import pytest

from dagster import (
    graph,
    SensorDefinition,
)
from dagster.core.errors import DagsterInvalidDefinitionError


def test_jobs_attr():
    def eval_fn():
        pass

    @graph
    def my_graph():
        pass

    sensor = SensorDefinition(evaluation_fn=eval_fn, job=my_graph)
    assert sensor.jobs[0].name == my_graph.name

    sensor = SensorDefinition(evaluation_fn=eval_fn, pipeline_name="my_pipeline")
    with pytest.raises(
        DagsterInvalidDefinitionError, match="No jobs were provided to SensorDefinition."
    ):
        sensor.jobs()


def test_direct_sensor_definition_instantiation():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Must provide evaluation_fn to SensorDefinition."
    ):
        SensorDefinition()
