from enum import Enum

from dagster import check


class EventType(Enum):
    PIPELINE_START = 'PIPELINE_START'
    PIPELINE_SUCCESS = 'PIPELINE_SUCCESS'
    PIPELINE_FAILURE = 'PIPELINE_FAILURE'
    UNCATEGORIZED = 'UNCATEGORIZED'


class ExecutionEvents:
    def __init__(self, context):
        self.context = context

    def pipeline_start(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Beginning execution of pipeline {pipeline}'.format(pipeline=self.pipeline_name()),
            event_type=EventType.PIPELINE_START.value,
        )

    def pipeline_success(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Completing successful execution of pipeline {pipeline}'.format(
                pipeline=self.pipeline_name(),
            ),
            event_type=EventType.PIPELINE_SUCCESS.value,
        )

    def pipeline_failure(self):
        self.check_pipeline_in_context()
        self.context.info(
            'Completing failing execution of pipeline {pipeline}'.format(
                pipeline=self.pipeline_name()
            ),
            event_type=EventType.PIPELINE_FAILURE.value,
        )

    def pipeline_name(self):
        return self.context.get_context_value('pipeline')

    def check_pipeline_in_context(self):
        check.invariant(
            self.context.has_context_value('pipeline'),
            'Must have pipeline context value',
        )
