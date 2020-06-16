# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[in_memory_instance_in_process_env] 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Failure',
            'label': 'always_false',
            'metadataEntries': [
                {
                    'description': None,
                    'jsonString': '{"reason": "Relentless pessimism."}',
                    'label': 'data'
                }
            ],
            'success': False
        },
        'level': 'DEBUG',
        'message': 'Failure',
        'step': {
            'key': 'emit_failed_expectation.compute',
            'solidHandleID': 'emit_failed_expectation'
        }
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[in_memory_instance_in_process_env] 2'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Successful',
            'label': 'always_true',
            'metadataEntries': [
                {
                    'description': None,
                    'jsonString': '{"reason": "Just because."}',
                    'label': 'data'
                }
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Successful',
        'step': {
            'key': 'emit_successful_expectation.compute',
            'solidHandleID': 'emit_successful_expectation'
        }
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[in_memory_instance_in_process_env] 3'] = [
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
        'step': {
            'key': 'emit_successful_expectation_no_metadata.compute',
            'solidHandleID': 'emit_successful_expectation_no_metadata'
        }
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_sync_run_launcher_in_process_env] 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Failure',
            'label': 'always_false',
            'metadataEntries': [
                {
                    'description': None,
                    'jsonString': '{"reason": "Relentless pessimism."}',
                    'label': 'data'
                }
            ],
            'success': False
        },
        'level': 'DEBUG',
        'message': 'Failure',
        'step': {
            'key': 'emit_failed_expectation.compute',
            'solidHandleID': 'emit_failed_expectation'
        }
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_sync_run_launcher_in_process_env] 2'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Successful',
            'label': 'always_true',
            'metadataEntries': [
                {
                    'description': None,
                    'jsonString': '{"reason": "Just because."}',
                    'label': 'data'
                }
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Successful',
        'step': {
            'key': 'emit_successful_expectation.compute',
            'solidHandleID': 'emit_successful_expectation'
        }
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_sync_run_launcher_in_process_env] 3'] = [
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
        'step': {
            'key': 'emit_successful_expectation_no_metadata.compute',
            'solidHandleID': 'emit_successful_expectation_no_metadata'
        }
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_cli_api_run_launcher_in_process_env] 1'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Failure',
            'label': 'always_false',
            'metadataEntries': [
                {
                    'description': None,
                    'jsonString': '{"reason": "Relentless pessimism."}',
                    'label': 'data'
                }
            ],
            'success': False
        },
        'level': 'DEBUG',
        'message': 'Failure',
        'step': {
            'key': 'emit_failed_expectation.compute',
            'solidHandleID': 'emit_failed_expectation'
        }
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_cli_api_run_launcher_in_process_env] 2'] = [
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': 'Successful',
            'label': 'always_true',
            'metadataEntries': [
                {
                    'description': None,
                    'jsonString': '{"reason": "Just because."}',
                    'label': 'data'
                }
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Successful',
        'step': {
            'key': 'emit_successful_expectation.compute',
            'solidHandleID': 'emit_successful_expectation'
        }
    }
]

snapshots['TestExpectations.test_basic_expectations_within_compute_step_events[sqlite_with_cli_api_run_launcher_in_process_env] 3'] = [
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
        'step': {
            'key': 'emit_successful_expectation_no_metadata.compute',
            'solidHandleID': 'emit_successful_expectation_no_metadata'
        }
    }
]

snapshots['TestExpectations.test_basic_input_output_expectations[in_memory_instance_in_process_env] 1'] = [
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
        'step': {
            'key': 'df_expectations_solid.compute',
            'solidHandleID': 'df_expectations_solid'
        }
    },
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': None,
            'label': 'other_expectation',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation other_expectation passed',
        'step': {
            'key': 'df_expectations_solid.compute',
            'solidHandleID': 'df_expectations_solid'
        }
    }
]

snapshots['TestExpectations.test_basic_input_output_expectations[sqlite_with_sync_run_launcher_in_process_env] 1'] = [
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
        'step': {
            'key': 'df_expectations_solid.compute',
            'solidHandleID': 'df_expectations_solid'
        }
    },
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': None,
            'label': 'other_expectation',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation other_expectation passed',
        'step': {
            'key': 'df_expectations_solid.compute',
            'solidHandleID': 'df_expectations_solid'
        }
    }
]

snapshots['TestExpectations.test_basic_input_output_expectations[sqlite_with_cli_api_run_launcher_in_process_env] 1'] = [
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
        'step': {
            'key': 'df_expectations_solid.compute',
            'solidHandleID': 'df_expectations_solid'
        }
    },
    {
        '__typename': 'StepExpectationResultEvent',
        'expectationResult': {
            'description': None,
            'label': 'other_expectation',
            'metadataEntries': [
            ],
            'success': True
        },
        'level': 'DEBUG',
        'message': 'Expectation other_expectation passed',
        'step': {
            'key': 'df_expectations_solid.compute',
            'solidHandleID': 'df_expectations_solid'
        }
    }
]
