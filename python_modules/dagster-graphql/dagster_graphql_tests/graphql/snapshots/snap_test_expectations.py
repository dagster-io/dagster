# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': 'Failure',
            'label': 'always_false',
            'metadataEntries': [
                {
                    '__typename': 'EventJsonMetadataEntry',
                    'description': None,
                    'jsonString': '{"reason": "Relentless pessimism."}',
                    'label': 'data'
                }
            ],
            'success': False
        },
        'level': 'DEBUG',
        'message': 'Failure',
        'runId': '<runId dummy value>',
        'solidHandleID': 'emit_failed_expectation',
        'stepKey': 'emit_failed_expectation',
        'timestamp': '<timestamp dummy value>'
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_default_run_launcher_deployed_grpc_env] 2'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': 'Successful',
            'label': 'always_true',
            'metadataEntries': [
                {
                    '__typename': 'EventJsonMetadataEntry',
                    'description': None,
                    'jsonString': '{"reason": "Just because."}',
                    'label': 'data'
                }
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Successful',
        'runId': '<runId dummy value>',
        'solidHandleID': 'emit_successful_expectation',
        'stepKey': 'emit_successful_expectation',
        'timestamp': '<timestamp dummy value>'
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_default_run_launcher_deployed_grpc_env] 3'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': 'Successful',
            'label': 'no_metadata',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Successful',
        'runId': '<runId dummy value>',
        'solidHandleID': 'emit_successful_expectation_no_metadata',
        'stepKey': 'emit_successful_expectation_no_metadata',
        'timestamp': '<timestamp dummy value>'
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': 'Failure',
            'label': 'always_false',
            'metadataEntries': [
                {
                    '__typename': 'EventJsonMetadataEntry',
                    'description': None,
                    'jsonString': '{"reason": "Relentless pessimism."}',
                    'label': 'data'
                }
            ],
            'success': False
        },
        'level': 'DEBUG',
        'message': 'Failure',
        'runId': '<runId dummy value>',
        'solidHandleID': 'emit_failed_expectation',
        'stepKey': 'emit_failed_expectation',
        'timestamp': '<timestamp dummy value>'
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_default_run_launcher_managed_grpc_env] 2'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': 'Successful',
            'label': 'always_true',
            'metadataEntries': [
                {
                    '__typename': 'EventJsonMetadataEntry',
                    'description': None,
                    'jsonString': '{"reason": "Just because."}',
                    'label': 'data'
                }
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Successful',
        'runId': '<runId dummy value>',
        'solidHandleID': 'emit_successful_expectation',
        'stepKey': 'emit_successful_expectation',
        'timestamp': '<timestamp dummy value>'
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_default_run_launcher_managed_grpc_env] 3'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': 'Successful',
            'label': 'no_metadata',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Successful',
        'runId': '<runId dummy value>',
        'solidHandleID': 'emit_successful_expectation_no_metadata',
        'stepKey': 'emit_successful_expectation_no_metadata',
        'timestamp': '<timestamp dummy value>'
    }
]

snapshots['TestExpectations.test_basic_input_output_expectations[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': None,
            'label': 'some_expectation',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation some_expectation passed',
        'runId': '<runId dummy value>',
        'solidHandleID': 'df_expectations_solid',
        'stepKey': 'df_expectations_solid',
        'timestamp': '<timestamp dummy value>'
    },
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': None,
            'label': 'other_expectation',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation other_expectation passed',
        'runId': '<runId dummy value>',
        'solidHandleID': 'df_expectations_solid',
        'stepKey': 'df_expectations_solid',
        'timestamp': '<timestamp dummy value>'
    }
]

snapshots['TestExpectations.test_basic_input_output_expectations[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': None,
            'label': 'some_expectation',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation some_expectation passed',
        'runId': '<runId dummy value>',
        'solidHandleID': 'df_expectations_solid',
        'stepKey': 'df_expectations_solid',
        'timestamp': '<timestamp dummy value>'
    },
    {
        '__typename': 'StepExpectationResultEvent',
        'eventType': 'STEP_EXPECTATION_RESULT',
        'expectationResult': {
            'description': None,
            'label': 'other_expectation',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation other_expectation passed',
        'runId': '<runId dummy value>',
        'solidHandleID': 'df_expectations_solid',
        'stepKey': 'df_expectations_solid',
        'timestamp': '<timestamp dummy value>'
    }
]
