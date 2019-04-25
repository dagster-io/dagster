# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_successful_pipeline_reexecution 1'] = {
    'startPipelineExecution': {
        '__typename': 'StartPipelineExecutionSuccess',
        'run': {
            'logs': {
                'nodes': [
                    {
                        '__typename': 'PipelineStartEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'INPUT_THUNK'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'input_thunk_output',
                        'step': {
                            'key': 'sum_solid.inputs.num.read',
                            'kind': 'INPUT_THUNK'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'TRANSFORM'
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_solid.transform',
                            'kind': 'TRANSFORM'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'INPUT_EXPECTATION'
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'expectation_value',
                        'step': {
                            'key': 'df_expectations_solid.output.sum_df.expectation.some_expectation',
                            'kind': 'INPUT_EXPECTATION'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'TRANSFORM'
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_sq_solid.transform',
                            'kind': 'TRANSFORM'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'JOIN'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'join_output',
                        'step': {
                            'key': 'df_expectations_solid.output.sum_df.expectations.join',
                            'kind': 'JOIN'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'TRANSFORM'
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'result',
                        'step': {
                            'key': 'df_expectations_solid.transform',
                            'kind': 'TRANSFORM'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'OUTPUT_EXPECTATION'
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'expectation_value',
                        'step': {
                            'key': 'df_expectations_solid.output.result.expectation.other_expectation',
                            'kind': 'OUTPUT_EXPECTATION'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'JOIN'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'join_output',
                        'step': {
                            'key': 'df_expectations_solid.output.result.expectations.join',
                            'kind': 'JOIN'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'PipelineSuccessEvent',
                        'level': 'INFO'
                    }
                ]
            },
            'pipeline': {
                'name': 'pandas_hello_world'
            }
        }
    }
}

snapshots['test_successful_pipeline_reexecution 2'] = {
    'startPipelineExecution': {
        '__typename': 'StartPipelineExecutionSuccess',
        'run': {
            'logs': {
                'nodes': [
                    {
                        '__typename': 'PipelineStartEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'TRANSFORM'
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'INFO',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_sq_solid.transform',
                            'kind': 'TRANSFORM'
                        },
                        'storageMode': 'FILESYSTEM'
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'PipelineSuccessEvent',
                        'level': 'INFO'
                    }
                ]
            },
            'pipeline': {
                'name': 'pandas_hello_world'
            }
        }
    }
}
