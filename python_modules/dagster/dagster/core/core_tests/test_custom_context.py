import pytest
import dagster
from dagster import config
from dagster.core.decorators import (solid, with_context)
from dagster.core.definitions import OutputDefinition
from dagster.core.execution import execute_pipeline


def test_default_context():
    @solid(
        inputs=[],
        output=OutputDefinition(),
    )
    @with_context
    def default_context_transform(context):
        assert context.args == {'arg_one': 'value'}

    pipeline = dagster.pipeline(solids=[default_context_transform])
    environment = config.Environment(
        sources={}, context=config.Context('default', {'arg_one': 'value_one'})
    )

    execute_pipeline()
