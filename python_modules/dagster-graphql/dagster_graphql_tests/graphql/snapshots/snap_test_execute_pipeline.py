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
                        'intermediateMaterialization': {
                            'description': None
                        },
                        'level': 'INFO',
                        'outputName': 'input_thunk_output',
                        'step': {
                            'key': 'sum_solid.inputs.num.read',
                            'kind': 'INPUT_THUNK'
                        }
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
                        'intermediateMaterialization': {
                            'description': None
                        },
                        'level': 'INFO',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_solid.transform',
                            'kind': 'TRANSFORM'
                        }
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
                        'intermediateMaterialization': {
                            'description': None
                        },
                        'level': 'INFO',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_sq_solid.transform',
                            'kind': 'TRANSFORM'
                        }
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
                        'intermediateMaterialization': {
                            'description': None
                        },
                        'level': 'INFO',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_sq_solid.transform',
                            'kind': 'TRANSFORM'
                        }
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
