# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_success_whole_execution_plan_with_in_memory_config 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_sq_solid.compute".',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "sum_df" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_sq_solid.compute" in {N}ms.',
                'stepKey': 'sum_sq_solid.compute'
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
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'stepKey': 'sum_solid.compute'
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
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'stepKey': 'sum_solid.compute'
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
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_sq_solid.compute".',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Retrieved intermediate object for input sum_df in filesystem object store using pickle.',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "sum_df" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_sq_solid.compute" in {N}ms.',
                'stepKey': 'sum_sq_solid.compute'
            }
        ]
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_in_memory_instance_in_process_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_in_memory_instance_out_of_process_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_in_memory_instance_multi_location] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_sqlite_instance_in_process_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_sqlite_instance_out_of_process_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_sqlite_instance_multi_location] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
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
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['test_pipeline_not_found_error_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'PipelineNotFoundError',
        'pipelineName': 'nope'
    }
}

snapshots['test_success_whole_execution_plan 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_sq_solid.compute".',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Retrieved intermediate object for input sum_df in filesystem object store using pickle.',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "sum_df" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_sq_solid.compute" in {N}ms.',
                'stepKey': 'sum_sq_solid.compute'
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
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_solid.compute".',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "num" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_solid.compute" in {N}ms.',
                'stepKey': 'sum_solid.compute'
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'message': 'Started execution of step "sum_sq_solid.compute".',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Retrieved intermediate object for input sum_df in filesystem object store using pickle.',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'message': 'Got input "sum_df" of type "PoorMansDataFrame". (Type check passed).',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'message': 'Yielded output "result" of type "PoorMansDataFrame". (Type check passed).',
                'outputName': 'result',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ObjectStoreOperationEvent',
                'message': 'Stored intermediate object for output result in filesystem object store using pickle.',
                'stepKey': 'sum_sq_solid.compute'
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'message': 'Finished execution of step "sum_sq_solid.compute" in {N}ms.',
                'stepKey': 'sum_sq_solid.compute'
            }
        ]
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_in_memory_instance_grpc] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_sqlite_instance_deployed_grpc] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_sqlite_instance_grpc] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_postgres_instance_grpc] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_postgres_instance_in_process_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_postgres_instance_out_of_process_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_postgres_instance_multi_location] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_sqlite_instance_managed_grpc_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_sqlite_instance_deployed_grpc_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}

snapshots['TestExecutionPlan.test_invalid_config_fetch_execute_plan[readonly_in_memory_instance_managed_grpc_env] 1'] = {
    'executionPlanOrError': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Invalid scalar at path root:solids:sum_solid:inputs:num'
            }
        ],
        'pipelineName': 'csv_hello_world'
    }
}
