# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

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
                },
                'tag': 'INPUT_THUNK'
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
                },
                'tag': 'TRANSFORM'
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
                },
                'tag': 'TRANSFORM'
            }
        ]
    }
}

snapshots['test_smoke_test_config_type_system 1'] = {
    'pipelines': {
        'nodes': [
            {
                'configTypes': [
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context_one'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context_two'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context_with_resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'resource_one'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    }
                ],
                'name': 'context_config_pipeline'
            },
            {
                'configTypes': [
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'field_one'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'field_three'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'field_two'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'a_solid_with_three_field_config'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    }
                ],
                'name': 'more_complicated_config'
            },
            {
                'configTypes': [
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'field_five_int'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'field_four_str'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'field_six_nullable_int_list'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'field_one'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'field_three'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'field_two'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'nested_field'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'a_solid_with_multilayered_config'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    }
                ],
                'name': 'more_complicated_nested_config'
            },
            {
                'configTypes': [
                    {
                        'description': None,
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'return_hello'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    }
                ],
                'name': 'no_config_pipeline'
            },
            {
                'configTypes': [
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'inputs'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'sum_solid'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'sum_sq_solid'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'num'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    }
                ],
                'name': 'pandas_hello_world'
            },
            {
                'configTypes': [
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'inputs'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'sum_solid'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'sum_sq_solid'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'num'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    }
                ],
                'name': 'pandas_hello_world_df_input'
            },
            {
                'configTypes': [
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'inputs'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'sum_solid'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'num'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    }
                ],
                'name': 'pandas_hello_world_two'
            },
            {
                'configTypes': [
                    {
                        'description': None,
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'takes_an_enum'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'values': [
                            {
                                'description': 'An enum value.',
                                'value': 'ENUM_VALUE'
                            }
                        ]
                    }
                ],
                'name': 'pipeline_with_enum_config'
            },
            {
                'configTypes': [
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'solid_with_list'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    }
                ],
                'name': 'pipeline_with_list'
            },
            {
                'configTypes': [
                    {
                        'description': None,
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': 'A configuration dictionary with typed fields',
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'solids'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'return_any'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'return_bool'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'return_int'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'return_str'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True
                    },
                    {
                        'description': '',
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    },
                    {
                        'description': None,
                        'fields': [
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True
                    }
                ],
                'name': 'scalar_output_pipeline'
            }
        ]
    }
}
