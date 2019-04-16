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
            'name': 'pandas_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'input_thunk_output',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                },
                'valueRepr': '''   num1  num2
0     1     2
1     3     4'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_sq_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum  sum_sq
0     1     2    3       9
1     3     4    7      49'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_sq_solid.transform'
                }
            }
        ]
    }
}

snapshots['test_success_whole_execution_plan_with_filesystem_config 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'pandas_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'input_thunk_output',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                },
                'valueRepr': '''   num1  num2
0     1     2
1     3     4'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_sq_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum  sum_sq
0     1     2    3       9
1     3     4    7      49'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_sq_solid.transform'
                }
            }
        ]
    }
}

snapshots['test_success_whole_execution_plan_with_in_memory_config 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'pandas_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'input_thunk_output',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                },
                'valueRepr': '''   num1  num2
0     1     2
1     3     4'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_sq_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum  sum_sq
0     1     2    3       9
1     3     4    7      49'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_sq_solid.transform'
                }
            }
        ]
    }
}

snapshots['test_invalid_config_execute_plan 1'] = {
    'executePlan': {
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

snapshots['test_pipeline_not_found_error_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'PipelineNotFoundError',
        'pipelineName': 'nope'
    }
}

snapshots['test_successful_two_part_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'pandas_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'input_thunk_output',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                },
                'valueRepr': '''   num1  num2
0     1     2
1     3     4'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.transform'
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
            'name': 'pandas_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_sq_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum  sum_sq
0     1     2    3       9
1     3     4    7      49'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_sq_solid.transform'
                }
            }
        ]
    }
}

snapshots['test_successful_one_part_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'pandas_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'input_thunk_output',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                },
                'valueRepr': '''   num1  num2
0     1     2
1     3     4'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            }
        ]
    }
}
