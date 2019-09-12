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
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation some_expectation passed',
        'runId': '*******-****-****-****-************',
        'step': {
            'inputs': [
                {
                    'dependsOn': [
                        {
                            'key': 'sum_solid.compute'
                        }
                    ],
                    'name': 'sum_df',
                    'type': {
                        'key': 'PoorMansDataFrame_'
                    }
                }
            ],
            'key': 'df_expectations_solid.compute',
            'kind': 'COMPUTE',
            'metadata': [
            ],
            'outputs': [
                {
                    'name': 'result',
                    'type': {
                        'key': 'PoorMansDataFrame_'
                    }
                }
            ],
            'solidHandleID': 'df_expectations_solid'
        },
        'timestamp': '*************'
    },
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': None,
            'label': 'other_expecation',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation other_expecation passed',
        'runId': '*******-****-****-****-************',
        'step': {
            'inputs': [
                {
                    'dependsOn': [
                        {
                            'key': 'sum_solid.compute'
                        }
                    ],
                    'name': 'sum_df',
                    'type': {
                        'key': 'PoorMansDataFrame_'
                    }
                }
            ],
            'key': 'df_expectations_solid.compute',
            'kind': 'COMPUTE',
            'metadata': [
            ],
            'outputs': [
                {
                    'name': 'result',
                    'type': {
                        'key': 'PoorMansDataFrame_'
                    }
                }
            ],
            'solidHandleID': 'df_expectations_solid'
        },
        'timestamp': '*************'
    }
]

snapshots['test_basic_expectations_within_compute_step_events 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
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
        'runId': '*******-****-****-****-************',
        'step': {
            'inputs': [
            ],
            'key': 'emit_failed_expectation.compute',
            'kind': 'COMPUTE',
            'metadata': [
            ],
            'outputs': [
            ],
            'solidHandleID': 'emit_failed_expectation'
        },
        'timestamp': '*************'
    }
]

snapshots['test_basic_expectations_within_compute_step_events 2'] = [
    {
        '__typename': 'StepExpectationResultEvent',
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
        'runId': '*******-****-****-****-************',
        'step': {
            'inputs': [
            ],
            'key': 'emit_successful_expectation.compute',
            'kind': 'COMPUTE',
            'metadata': [
            ],
            'outputs': [
            ],
            'solidHandleID': 'emit_successful_expectation'
        },
        'timestamp': '*************'
    }
]

snapshots['test_basic_expectations_within_compute_step_events 3'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Successful',
            'label': 'no_metadata',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Successful',
        'runId': '*******-****-****-****-************',
        'step': {
            'inputs': [
            ],
            'key': 'emit_successful_expectation_no_metadata.compute',
            'kind': 'COMPUTE',
            'metadata': [
            ],
            'outputs': [
            ],
            'solidHandleID': 'emit_successful_expectation_no_metadata'
        },
        'timestamp': '*************'
    }
]
