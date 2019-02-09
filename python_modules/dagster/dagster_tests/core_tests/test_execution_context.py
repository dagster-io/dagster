import warnings
import uuid

from dagster import PipelineDefinition, solid, execute_pipeline
from dagster.utils.test import create_test_runtime_legacy_execution_context

# pylint: disable=W0212


def test_noarg_ctor():
    legacy_context = create_test_runtime_legacy_execution_context()
    assert uuid.UUID(legacy_context.run_id)


def test_warning_on_context():
    @solid
    def log_something(context):
        context.context.info('hi')

    pipeline = PipelineDefinition(name='warning_on_context', solids=[log_something])

    with warnings.catch_warnings(record=True) as list_of_warnings:
        result = execute_pipeline(pipeline)
        assert result.success
        assert len(list_of_warnings) == 1
        warning = list_of_warnings[0]
        assert 'As of 3.0.2 the context property is deprecated.' in str(warning.message)


def test_warning_on_config():
    @solid
    def check_config_is_none(context):
        assert context.config is None

    pipeline = PipelineDefinition(name='warning_on_config', solids=[check_config_is_none])

    with warnings.catch_warnings(record=True) as list_of_warnings:
        result = execute_pipeline(pipeline)
        assert result.success
        assert len(list_of_warnings) == 1
        warning = list_of_warnings[0]
        assert 'As of 3.0.2 the config property is deprecated.' in str(warning.message)
