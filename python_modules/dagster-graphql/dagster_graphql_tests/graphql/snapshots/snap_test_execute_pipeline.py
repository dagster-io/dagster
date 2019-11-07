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
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'EngineEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_solid.compute',
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
                        '__typename': 'ObjectStoreOperationEvent',
                        'level': 'DEBUG',
                        'operationResult': {
                            'metadataEntries': [
                                {
                                    'description': None,
                                    'label': 'key',
                                    'path': 'DUMMY_PATH'
                                }
                            ],
                            'op': 'SET_OBJECT'
                        },
                        'step': {
                            'key': 'sum_solid.compute'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_solid.compute'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_sq_solid.compute',
                            'kind': 'COMPUTE'
                        }
                    },
                    {
                        '__typename': 'ObjectStoreOperationEvent',
                        'level': 'DEBUG',
                        'operationResult': {
                            'metadataEntries': [
                                {
                                    'description': None,
                                    'label': 'key',
                                    'path': 'DUMMY_PATH'
                                }
                            ],
                            'op': 'GET_OBJECT'
                        },
                        'step': {
                            'key': 'sum_sq_solid.compute'
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
                        '__typename': 'ObjectStoreOperationEvent',
                        'level': 'DEBUG',
                        'operationResult': {
                            'metadataEntries': [
                                {
                                    'description': None,
                                    'label': 'key',
                                    'path': 'DUMMY_PATH'
                                }
                            ],
                            'op': 'SET_OBJECT'
                        },
                        'step': {
                            'key': 'sum_sq_solid.compute'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_sq_solid.compute'
                        }
                    },
                    {
                        '__typename': 'EngineEvent',
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
            },
            'tags': [
            ]
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
                        '__typename': 'EngineEvent',
                        'level': 'DEBUG'
                    },
                    {
                        '__typename': 'ObjectStoreOperationEvent',
                        'level': 'DEBUG',
                        'operationResult': {
                            'metadataEntries': [
                                {
                                    'description': None,
                                    'label': 'key',
                                    'path': 'DUMMY_PATH'
                                }
                            ],
                            'op': 'CP_OBJECT'
                        },
                        'step': {
                            'key': 'sum_solid.compute'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepStartEvent',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_sq_solid.compute',
                            'kind': 'COMPUTE'
                        }
                    },
                    {
                        '__typename': 'ObjectStoreOperationEvent',
                        'level': 'DEBUG',
                        'operationResult': {
                            'metadataEntries': [
                                {
                                    'description': None,
                                    'label': 'key',
                                    'path': 'DUMMY_PATH'
                                }
                            ],
                            'op': 'GET_OBJECT'
                        },
                        'step': {
                            'key': 'sum_sq_solid.compute'
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
                        '__typename': 'ObjectStoreOperationEvent',
                        'level': 'DEBUG',
                        'operationResult': {
                            'metadataEntries': [
                                {
                                    'description': None,
                                    'label': 'key',
                                    'path': 'DUMMY_PATH'
                                }
                            ],
                            'op': 'SET_OBJECT'
                        },
                        'step': {
                            'key': 'sum_sq_solid.compute'
                        }
                    },
                    {
                        '__typename': 'ExecutionStepSuccessEvent',
                        'level': 'DEBUG',
                        'step': {
                            'key': 'sum_sq_solid.compute'
                        }
                    },
                    {
                        '__typename': 'EngineEvent',
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
            },
            'tags': [
            ]
        }
    }
}

snapshots['test_pipeline_reexecution_info_query 1'] = [
    'sum_sq_solid.compute'
]
