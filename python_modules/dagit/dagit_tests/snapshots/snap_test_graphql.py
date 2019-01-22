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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
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
                        'innerTypes': [
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
                                'name': 'field_two'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'field_three'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                        ],
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
                        'innerTypes': [
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
                                'name': 'field_four_str'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'field_five_int'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'field_six_nullable_int_list'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': 'List of Nullable.Int'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                                'name': 'field_two'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'field_three'
                            },
                            {
                                'description': None,
                                'isOptional': False,
                                'name': 'nested_field'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': 'List of Nullable.Int'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': 'List of Nullable.Int'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'List of Nullable.Int'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'List of Nullable.Int'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                        ],
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
                        'description': '',
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'description': None
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                        ],
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                        ],
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
                        'description': '',
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of Int'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'List of Int'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'List of Int'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                        ],
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
                        'description': '',
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'List of PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PandasHelloWorldDfInput.SumSqSolid.Outputs'
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'List of PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                        ],
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
                        'description': None,
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'value'
                            },
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'List of NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
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
                        'description': None,
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'value'
                            },
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'value'
                            },
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'value'
                            },
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
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
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnAny.Outputs'
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnAny.Outputs'
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnBool.Outputs'
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
                        'innerTypes': [
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
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
                                'name': 'return_str'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'return_int'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'return_bool'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'return_any'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of ScalarOutputPipeline.ReturnAny.Outputs'
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'value'
                            },
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
            },
            {
                'configTypes': [
                    {
                        'description': None,
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'value'
                            },
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
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
                        'innerTypes': [
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
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'List of PipelineWithEnumConfig.TakesAnEnum.Outputs'
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
                        'innerTypes': [
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
                        'innerTypes': [
                            {
                                'description': ''
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
                        'innerTypes': [
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'List of PipelineWithEnumConfig.TakesAnEnum.Outputs'
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
                        'innerTypes': [
                            {
                                'description': 'List of PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
                            },
                            {
                                'description': None
                            },
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': None
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
                        'innerTypes': [
                            {
                                'description': ''
                            },
                            {
                                'description': None
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
                            },
                            {
                                'description': 'A configuration dictionary with typed fields'
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
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False
                    },
                    {
                        'description': None,
                        'innerTypes': [
                        ],
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
            }
        ]
    }
}
