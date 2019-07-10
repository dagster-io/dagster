# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_basic_input_output_expectations 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': None,
            'label': 'some_expectation',
            'metadataEntries': [],
            'success': True,
        },
        'level': 'DEBUG',
        'message': 'DagsterEventType.STEP_EXPECTATION_RESULT for step df_expectations_solid.compute',
        'step': {'key': 'df_expectations_solid.compute', 'solidHandleID': 'df_expectations_solid'},
    },
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': None,
            'label': 'other_expecation',
            'metadataEntries': [],
            'success': True,
        },
        'level': 'DEBUG',
        'message': 'DagsterEventType.STEP_EXPECTATION_RESULT for step df_expectations_solid.compute',
        'step': {'key': 'df_expectations_solid.compute', 'solidHandleID': 'df_expectations_solid'},
    },
]

snapshots['test_basic_expectations_within_compute_step_events 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Failure',
            'label': 'always_false',
            'metadataEntries': [
                {
                    'description': None,
                    'jsonString': '{"reason": "Relentless pessimism."}',
                    'label': 'data',
                }
            ],
            'success': False,
        },
        'level': 'DEBUG',
        'message': 'DagsterEventType.STEP_EXPECTATION_RESULT for step emit_failed_expectation.compute',
        'step': {
            'key': 'emit_failed_expectation.compute',
            'solidHandleID': 'emit_failed_expectation',
        },
    }
]

snapshots['test_basic_expectations_within_compute_step_events 2'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Successful',
            'label': 'always_true',
            'metadataEntries': [
                {'description': None, 'jsonString': '{"reason": "Just because."}', 'label': 'data'}
            ],
            'success': True,
        },
        'level': 'DEBUG',
        'message': 'DagsterEventType.STEP_EXPECTATION_RESULT for step emit_successful_expectation.compute',
        'step': {
            'key': 'emit_successful_expectation.compute',
            'solidHandleID': 'emit_successful_expectation',
        },
    }
]

snapshots['test_basic_expectations_within_compute_step_events 3'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Successful',
            'label': 'no_metadata',
            'metadataEntries': [],
            'success': True,
        },
        'level': 'DEBUG',
        'message': 'DagsterEventType.STEP_EXPECTATION_RESULT for step emit_successful_expectation_no_metadata.compute',
        'step': {
            'key': 'emit_successful_expectation_no_metadata.compute',
            'solidHandleID': 'emit_successful_expectation_no_metadata',
        },
    }
]
