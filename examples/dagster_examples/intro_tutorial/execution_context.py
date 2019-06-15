# pylint: disable=no-value-for-parameter

from dagster import pipeline, solid


@solid
def debug_message(context):
    context.log.debug('A debug message.')
    return 'foo'


@solid
def error_message(context):
    context.log.error('An error occurred.')


@pipeline
def execution_context_pipeline(_):
    debug_message()
    error_message()


def define_execution_context_pipeline():
    return execution_context_pipeline
