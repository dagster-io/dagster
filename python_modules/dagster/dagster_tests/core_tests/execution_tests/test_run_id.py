import uuid

from dagster import solid, PipelineDefinition, execute_pipeline, RunConfig


def test_default_run_id():
    called = {}

    @solid
    def check_run_id(context):
        called['yes'] = True
        assert uuid.UUID(context.run_id)

    pipeline = PipelineDefinition(solids=[check_run_id])

    execute_pipeline(pipeline)

    assert called['yes']


def test_provided_run_id():
    called = {}

    @solid
    def check_run_id(context):
        called['yes'] = True
        assert context.run_id == 'given'

    pipeline = PipelineDefinition(solids=[check_run_id])

    execute_pipeline(pipeline, run_config=RunConfig(run_id='given'))

    assert called['yes']
