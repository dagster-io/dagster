# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

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
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            }
        ]
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
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), ('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), ('sum_sq', 49)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
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
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), ('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), ('sum_sq', 49)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
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
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), ('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), ('sum_sq', 49)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
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
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
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
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_sq_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), ('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), ('sum_sq', 49)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
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
                'message': 'Value at path root:solids:sum_solid:inputs:num is not valid. Expected "Path"'
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
                'message': 'Value at path root:solids:sum_solid:inputs:num is not valid. Expected "Path"'
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

snapshots['test_pipeline_with_execution_metadata 1'] = {
    'executionPlan': {
        '__typename': 'ExecutionPlan',
        'pipeline': {
            'name': 'pipeline_with_step_metadata'
        },
        'steps': [
            {
                'inputs': [
                ],
                'key': 'solid_metadata_creation.compute',
                'kind': 'COMPUTE',
                'metadata': [
                    {
                        'key': 'computed',
                        'value': 'foobar1'
                    }
                ],
                'outputs': [
                ],
                'solidHandleID': 'solid_metadata_creation'
            }
        ]
    }
}
