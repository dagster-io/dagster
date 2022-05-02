import pytest

from dagster import SensorDefinition, graph
from dagster.core.errors import DagsterInvalidDefinitionError


def test_jobs_attr():
    def eval_fn():
        pass

    @graph
    def my_graph():
        pass

    sensor = SensorDefinition(evaluation_fn=eval_fn, job=my_graph)
    assert sensor.job.name == my_graph.name

    sensor = SensorDefinition(evaluation_fn=eval_fn, pipeline_name="my_pipeline")
    with pytest.raises(
        DagsterInvalidDefinitionError, match="No job was provided to SensorDefinition."
    ):
        sensor.job  # pylint: disable=pointless-statement

    @graph
    def my_second_graph():
        pass

    sensor = SensorDefinition(evaluation_fn=eval_fn, jobs=[my_graph, my_second_graph])
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Job property not available when SensorDefinition has multiple jobs.",
    ):
        sensor.job  # pylint: disable=pointless-statement


def test_direct_sensor_definition_instantiation():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Must provide evaluation_fn to SensorDefinition."
    ):
        SensorDefinition()
