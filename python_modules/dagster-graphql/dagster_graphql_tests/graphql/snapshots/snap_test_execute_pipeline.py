# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_pipeline_reexecution_info_query 1'] = [
    'sum_sq_solid.compute'
]

snapshots['test_successful_pipeline_reexecution 1'] = {
    'startPipelineExecution': {
        '__typename': 'StartPipelineExecutionSuccess',
        'run': {
            'logs': {
                'nodes': [
                    {
                        '__typename': 'PipelineStartEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'DEBUG',
                        'step': {
                            'kind': 'COMPUTE'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepInputEvent',
                        'inputName': 'num',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_solid.compute',
                            'kind': 'COMPUTE'
                        },
                        'typeCheck': {
                            'description': None,
                            'label': 'num',
                            'metadataEntries': [
                            ]
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'DEBUG',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_solid.compute',
                            'kind': 'COMPUTE'
                        },
                        'typeCheck': {
                            'description': None,
                            'label': 'result',
                            'metadataEntries': [
                            ]
                        }
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'DEBUG',
                        'step': {
                            'kind': 'COMPUTE'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepInputEvent',
                        'inputName': 'sum_df',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_sq_solid.compute',
                            'kind': 'COMPUTE'
                        },
                        'typeCheck': {
                            'description': None,
                            'label': 'sum_df',
                            'metadataEntries': [
                            ]
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'DEBUG',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_sq_solid.compute',
                            'kind': 'COMPUTE'
                        },
                        'typeCheck': {
                            'description': None,
                            'label': 'result',
                            'metadataEntries': [
                            ]
                        }
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'PipelineSuccessEvent',
                        'level': 'DEBUG'
                    }
                ]
            },
            'pipeline': {
                'name': 'csv_hello_world'
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
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'DEBUG',
                        'step': {
                            'kind': 'COMPUTE'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepInputEvent',
                        'inputName': 'sum_df',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_sq_solid.compute',
                            'kind': 'COMPUTE'
                        },
                        'typeCheck': {
                            'description': None,
                            'label': 'sum_df',
                            'metadataEntries': [
                            ]
                        }
                    },
                    {
                        '__typename': 'LogMessageEvent',
                        'level': 'INFO'
                    },
                    {
                        '__typename': 'ExecutionStepOutputEvent',
                        'level': 'DEBUG',
                        'outputName': 'result',
                        'step': {
                            'key': 'sum_sq_solid.compute',
                            'kind': 'COMPUTE'
                        },
                        'typeCheck': {
                            'description': None,
                            'label': 'result',
                            'metadataEntries': [
                            ]
                        }
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'PipelineSuccessEvent',
                        'level': 'DEBUG'
                    }
                ]
            },
            'pipeline': {
                'name': 'csv_hello_world'
            }
        }
    }
}
