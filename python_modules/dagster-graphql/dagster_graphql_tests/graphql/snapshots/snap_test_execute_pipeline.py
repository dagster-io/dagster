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
                            'description': None,
                            'path': '/tmp/dagster/runs/2587a620-a059-48c2-817b-3bb8cb8af39e/files/intermediates/sum_solid.inputs.num.read/input_thunk_output'
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
                            'description': None,
                            'path': '/tmp/dagster/runs/2587a620-a059-48c2-817b-3bb8cb8af39e/files/intermediates/sum_solid.transform/result'
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
                            'kind': 'INPUT_EXPECTATION'
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'intermediateMaterialization': {
                            'description': None,
                            'path': '/tmp/dagster/runs/2587a620-a059-48c2-817b-3bb8cb8af39e/files/intermediates/df_expectations_solid.output.sum_df.expectation.some_expectation/expectation_value'
                        },
                        'level': 'INFO',
                        'outputName': 'expectation_value',
                        'step': {
                            'key': 'df_expectations_solid.output.sum_df.expectation.some_expectation',
                            'kind': 'INPUT_EXPECTATION'
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
                            'description': None,
                            'path': '/tmp/dagster/runs/2587a620-a059-48c2-817b-3bb8cb8af39e/files/intermediates/sum_sq_solid.transform/result'
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
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'INFO',
                        'step': {
                            'kind': 'JOIN'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'intermediateMaterialization': {
                            'description': None,
                            'path': '/tmp/dagster/runs/2587a620-a059-48c2-817b-3bb8cb8af39e/files/intermediates/df_expectations_solid.output.sum_df.expectations.join/join_output'
                        },
                        'level': 'INFO',
                        'outputName': 'join_output',
                        'step': {
                            'key': 'df_expectations_solid.output.sum_df.expectations.join',
                            'kind': 'JOIN'
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
                            'description': None,
                            'path': '/tmp/dagster/runs/2587a620-a059-48c2-817b-3bb8cb8af39e/files/intermediates/df_expectations_solid.transform/result'
                        },
                        'level': 'INFO',
                        'outputName': 'result',
                        'step': {
                            'key': 'df_expectations_solid.transform',
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
                            'kind': 'OUTPUT_EXPECTATION'
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'intermediateMaterialization': {
                            'description': None,
                            'path': '/tmp/dagster/runs/2587a620-a059-48c2-817b-3bb8cb8af39e/files/intermediates/df_expectations_solid.output.result.expectation.other_expectation/expectation_value'
                        },
                        'level': 'INFO',
                        'outputName': 'expectation_value',
                        'step': {
                            'key': 'df_expectations_solid.output.result.expectation.other_expectation',
                            'kind': 'OUTPUT_EXPECTATION'
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
                            'kind': 'JOIN'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'intermediateMaterialization': {
                            'description': None,
                            'path': '/tmp/dagster/runs/2587a620-a059-48c2-817b-3bb8cb8af39e/files/intermediates/df_expectations_solid.output.result.expectations.join/join_output'
                        },
                        'level': 'INFO',
                        'outputName': 'join_output',
                        'step': {
                            'key': 'df_expectations_solid.output.result.expectations.join',
                            'kind': 'JOIN'
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
                            'description': None,
                            'path': '/tmp/dagster/runs/ab21c375-13cb-4240-a161-e92c76444799/files/intermediates/sum_sq_solid.transform/result'
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
