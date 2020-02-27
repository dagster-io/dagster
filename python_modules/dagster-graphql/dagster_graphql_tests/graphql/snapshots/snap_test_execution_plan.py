# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_success_whole_execution_plan 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'EngineEvent',
                'message': 'Executing steps in process (pid: {N})',
                'step': None
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_sq_solid.compute".',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Retrieved intermediate object for input sum_df in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "sum_df" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_sq_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'EngineEvent',
                'message': 'Finished steps in process (pid: {N}) in {N}ms',
                'step': None
            }
        ]
    }
}

snapshots['test_success_whole_execution_plan_with_filesystem_config 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'EngineEvent',
                'message': 'Executing steps in process (pid: {N})',
                'step': None
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_sq_solid.compute".',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Retrieved intermediate object for input sum_df in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "sum_df" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_sq_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'EngineEvent',
                'message': 'Finished steps in process (pid: {N}) in {N}ms',
                'step': None
            }
        ]
    }
}

snapshots['test_success_whole_execution_plan_with_in_memory_config 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'EngineEvent',
                'message': 'Executing steps in process (pid: {N})',
                'step': None
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_sq_solid.compute".',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "sum_df" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_sq_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'EngineEvent',
                'message': 'Finished steps in process (pid: {N}) in {N}ms',
                'step': None
            }
        ]
    }
}

snapshots['test_successful_one_part_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'EngineEvent',
                'message': 'Executing steps in process (pid: {N})',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'EngineEvent',
                'message': 'Finished steps in process (pid: {N}) in {N}ms',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            }
        ]
    }
}

snapshots['test_successful_two_part_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'EngineEvent',
                'message': 'Executing steps in process (pid: {N})',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'EngineEvent',
                'message': 'Finished steps in process (pid: {N}) in {N}ms',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            }
        ]
    }
}

snapshots['test_successful_two_part_execute_plan 2'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'EngineEvent',
                'message': 'Executing steps in process (pid: {N})',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_sq_solid.compute".',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Retrieved intermediate object for input sum_df in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "sum_df" of type "PoorMansDataFrame". (Type check passed).',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_sq_solid.compute" in {N}ms.',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'EngineEvent',
                'message': 'Finished steps in process (pid: {N}) in {N}ms',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            }
        ]
    }
}

snapshots['test_invalid_config_fetch_execute_plan 1'] = {
    'executionPlan': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipeline': {
            'name': 'csv_hello_world'
        }
    }
}

snapshots['test_invalid_config_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipeline': {
            'name': 'csv_hello_world'
        }
    }
}

snapshots['test_pipeline_not_found_error_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'PipelineNotFoundError',
        'pipelineName': 'nope'
    }
}
