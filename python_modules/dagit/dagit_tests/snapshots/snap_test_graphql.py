# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_start_subplan_pipeline_not_found 1'] = {
    'startSubplanExecution': {
        '__typename': 'PipelineNotFoundError',
        'pipelineName': 'nope'
    }
}

snapshots['test_start_subplan_invalid_config 1'] = {
    'startSubplanExecution': {
        '__typename': 'PipelineConfigValidationInvalid',
        'errors': [
            {
                'message': 'Value at path root:solids:sum_solid:inputs:num:csv:path is not valid. Expected "Path"'
            }
        ],
        'pipeline': {
            'name': 'pandas_hello_world'
        }
    }
}

snapshots['test_successful_start_subplan 1'] = {
    'startSubplanExecution': {
        '__typename': 'StartSubplanExecutionSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'pandas_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'SuccessfulStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.transform'
                },
                'success': True,
                'valueRepr': '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
            }
        ]
    }
}

snapshots['test_user_error_pipeline 1'] = {
    'startSubplanExecution': {
        '__typename': 'StartSubplanExecutionSuccess',
        'hasFailures': True,
        'pipeline': {
            'name': 'naughty_programmer_pipeline'
        },
        'stepEvents': [
            {
                '__typename': 'StepFailureEvent',
                'errorMessage': '''Exception: bad programmer, bad
''',
                'step': {
                    'key': 'throw_a_thing.transform'
                },
                'success': False
            }
        ]
    }
}

snapshots['test_user_code_error_subplan 1'] = {
    'startSubplanExecution': {
        '__typename': 'StartSubplanExecutionSuccess',
        'hasFailures': True,
        'pipeline': {
            'name': 'naughty_programmer_pipeline'
        },
        'stepEvents': [
            {
                '__typename': 'StepFailureEvent',
                'errorMessage': '''Exception: bad programmer, bad
''',
                'step': {
                    'key': 'throw_a_thing.transform'
                },
                'success': False
            }
        ]
    }
}

snapshots['test_start_subplan_invalid_step_keys 1'] = {
    'startSubplanExecution': {
        '__typename': 'StartSubplanExecutionInvalidStepError',
        'invalidStepKey': 'nope'
    }
}

snapshots['test_invalid_subplan_missing_inputs 1'] = {
    'startSubplanExecution': {
        '__typename': 'InvalidSubplanMissingInputError',
        'missingInputName': 'num',
        'stepKey': 'sum_solid.transform'
    }
}

snapshots['test_start_subplan_invalid_output_name 1'] = {
    'startSubplanExecution': {
        '__typename': 'StartSubplanExecutionInvalidOutputError',
        'invalidOutputName': 'nope',
        'stepKey': 'sum_solid.transform'
    }
}

snapshots['test_start_subplan_invalid_input_name 1'] = {
    'startSubplanExecution': {
        '__typename': 'StartSubplanExecutionInvalidInputError',
        'invalidInputName': 'nope',
        'stepKey': 'sum_solid.transform'
    }
}

snapshots['test_query_execution_plan_snapshot 1'] = {
    'executionPlan': {
        '__typename': 'ExecutionPlan',
        'pipeline': {
            'name': 'pandas_hello_world'
        },
        'steps': [
            {
                'inputs': [
                ],
                'kind': 'INPUT_THUNK',
                'name': 'sum_solid.num.input_thunk',
                'outputs': [
                    {
                        'name': 'input_thunk_output',
                        'type': {
                            'name': 'PandasDataFrame'
                        }
                    }
                ],
                'solid': {
                    'name': 'sum_solid'
                }
            },
            {
                'inputs': [
                    {
                        'dependsOn': {
                            'name': 'sum_solid.num.input_thunk'
                        },
                        'name': 'num',
                        'type': {
                            'name': 'PandasDataFrame'
                        }
                    }
                ],
                'kind': 'TRANSFORM',
                'name': 'sum_solid.transform',
                'outputs': [
                    {
                        'name': 'result',
                        'type': {
                            'name': 'PandasDataFrame'
                        }
                    }
                ],
                'solid': {
                    'name': 'sum_solid'
                }
            },
            {
                'inputs': [
                    {
                        'dependsOn': {
                            'name': 'sum_solid.transform'
                        },
                        'name': 'sum_df',
                        'type': {
                            'name': 'PandasDataFrame'
                        }
                    }
                ],
                'kind': 'TRANSFORM',
                'name': 'sum_sq_solid.transform',
                'outputs': [
                    {
                        'name': 'result',
                        'type': {
                            'name': 'PandasDataFrame'
                        }
                    }
                ],
                'solid': {
                    'name': 'sum_sq_solid'
                }
            }
        ]
    }
}
