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
                                'configType': {
                                    'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context_one'
                            },
                            {
                                'configType': {
                                    'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context_two'
                            },
                            {
                                'configType': {
                                    'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context_with_resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo.Resources'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources'
                            },
                            {
                                'name': 'Dict.115'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne.Resources'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne.Resources'
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
                                'configType': {
                                    'name': 'Int'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo.Resources'
                            },
                            {
                                'name': 'Int'
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
                                'configType': {
                                    'name': 'Dict.115'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'Dict.115'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'resource_one'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
                            },
                            {
                                'name': 'Int'
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
                                'configType': {
                                    'name': 'Int'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Int'
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
                                'configType': {
                                    'name': 'ContextConfigPipeline.ContextConfig'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'ContextConfigPipeline.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'ContextConfigPipeline.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'ContextConfigPipeline.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextConfig'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne'
                            },
                            {
                                'name': 'ContextConfigPipeline.ExecutionConfig'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'ContextConfigPipeline.SolidsConfigDictionary'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo.Resources'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources'
                            },
                            {
                                'name': 'Dict.115'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne.Resources'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo'
                            },
                            {
                                'name': 'ContextConfigPipeline.ExpectationsConfig'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'field_one'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'field_two'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'field_three'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.117'
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
                                'configType': {
                                    'name': 'Dict.117'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.117'
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
                                'configType': {
                                    'name': 'MoreComplicatedConfig.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'MoreComplicatedConfig.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'MoreComplicatedConfig.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'MoreComplicatedConfig.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'MoreComplicatedConfig.ContextConfig'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ExpectationsConfig'
                            },
                            {
                                'name': 'Dict.116'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'MoreComplicatedConfig.SolidsConfigDictionary'
                            },
                            {
                                'name': 'MoreComplicatedConfig.SolidConfig.ASolidWithThreeFieldConfig'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ExecutionConfig'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.117'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'Dict.116'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.116'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'MoreComplicatedConfig.SolidConfig.ASolidWithThreeFieldConfig'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'a_solid_with_three_field_config'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.116'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedConfig.SolidConfig.ASolidWithThreeFieldConfig'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'field_four_str'
                            },
                            {
                                'configType': {
                                    'name': 'Int'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'field_five_int'
                            },
                            {
                                'configType': {
                                    'name': 'List.Nullable.Int'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'field_six_nullable_int_list'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Nullable.Int'
                            },
                            {
                                'name': 'List.Nullable.Int'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Int'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'field_one'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'field_two'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'field_three'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.118'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'nested_field'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.118'
                            },
                            {
                                'name': 'Nullable.Int'
                            },
                            {
                                'name': 'List.Nullable.Int'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.120'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default'
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
                                'configType': {
                                    'name': 'Dict.120'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.120'
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
                                'configType': {
                                    'name': 'MoreComplicatedNestedConfig.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'MoreComplicatedNestedConfig.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'MoreComplicatedNestedConfig.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'MoreComplicatedNestedConfig.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.118'
                            },
                            {
                                'name': 'Nullable.Int'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.120'
                            },
                            {
                                'name': 'List.Nullable.Int'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextConfig'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ExpectationsConfig'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.119'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ExecutionConfig'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.SolidsConfigDictionary'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'Dict.119'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.118'
                            },
                            {
                                'name': 'Nullable.Int'
                            },
                            {
                                'name': 'List.Nullable.Int'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'Dict.119'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'a_solid_with_multilayered_config'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.118'
                            },
                            {
                                'name': 'Nullable.Int'
                            },
                            {
                                'name': 'List.Nullable.Int'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'Dict.119'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'PandasHelloWorld.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.121'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.121'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorld.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.121'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'PandasHelloWorld.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorld.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorld.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorld.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextConfig'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorld.SolidsConfigDictionary'
                            },
                            {
                                'name': 'PandasHelloWorld.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Inputs'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'PandasHelloWorld.SolidConfig.SumSqSolid'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.121'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'PandasHelloWorld.ExpectationsConfig'
                            },
                            {
                                'name': 'PandasHelloWorld.ExecutionConfig'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'PandasHelloWorld.SumSolid.Inputs'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'inputs'
                            },
                            {
                                'configType': {
                                    'name': 'List.PandasHelloWorld.SumSolid.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Inputs'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'List.PandasHelloWorld.SumSqSolid.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'PandasHelloWorld.SolidConfig.SumSolid'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'sum_solid'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorld.SolidConfig.SumSqSolid'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'sum_sq_solid'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PandasHelloWorld.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Inputs'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'PandasHelloWorld.SolidConfig.SumSqSolid'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'Selector.30'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'num'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'Selector.26'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Selector.26'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.23'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.24'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.25'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.27'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.28'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.29'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.122'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default.Resources'
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
                                'configType': {
                                    'name': 'Dict.122'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.122'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'PandasHelloWorldTwo.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldTwo.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldTwo.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldTwo.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PandasHelloWorldTwo.ExpectationsConfig'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.ExecutionConfig'
                            },
                            {
                                'name': 'Dict.122'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.ContextConfig'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Inputs'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'List.PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'name': 'Selector.30'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'PandasHelloWorldTwo.SumSolid.Inputs'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'inputs'
                            },
                            {
                                'configType': {
                                    'name': 'List.PandasHelloWorldTwo.SumSolid.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'List.PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Inputs'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'PandasHelloWorldTwo.SolidConfig.SumSolid'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'sum_solid'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'List.PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Inputs'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Outputs'
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
                                'configType': {
                                    'name': 'Selector.30'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'num'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'Selector.26'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.23'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.24'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.25'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.27'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.28'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.29'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'PipelineWithList.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.123'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.123'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'PipelineWithList.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.123'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'PipelineWithList.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'PipelineWithList.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'PipelineWithList.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'PipelineWithList.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PipelineWithList.ExpectationsConfig'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'PipelineWithList.SolidsConfigDictionary'
                            },
                            {
                                'name': 'List.Int'
                            },
                            {
                                'name': 'PipelineWithList.SolidConfig.SolidWithList'
                            },
                            {
                                'name': 'PipelineWithList.ExecutionConfig'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.123'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PipelineWithList.ContextConfig'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'List.Int'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'List.Int'
                            },
                            {
                                'name': 'Int'
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
                                'configType': {
                                    'name': 'PipelineWithList.SolidConfig.SolidWithList'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'solid_with_list'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'List.Int'
                            },
                            {
                                'name': 'PipelineWithList.SolidConfig.SolidWithList'
                            },
                            {
                                'name': 'Int'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            },
                            {
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'sep'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.124'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.124'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.124'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SolidConfig.SumSqSolid'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.124'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ExpectationsConfig'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ExecutionConfig'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextConfig'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Inputs'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSolid.Outputs'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.SumSolid.Inputs'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'inputs'
                            },
                            {
                                'configType': {
                                    'name': 'List.PandasHelloWorldDfInput.SumSolid.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Inputs'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'List.PandasHelloWorldDfInput.SumSqSolid.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSqSolid.Outputs'
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
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.SolidConfig.SumSolid'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'sum_solid'
                            },
                            {
                                'configType': {
                                    'name': 'PandasHelloWorldDfInput.SolidConfig.SumSqSolid'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'sum_sq_solid'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SolidConfig.SumSqSolid'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Inputs'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSolid.Outputs'
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
                                'configType': {
                                    'name': 'Selector.30'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'num'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'Selector.26'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Selector.26'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.23'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.24'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.25'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.27'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'csv'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.28'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'parquet'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.29'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'table'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.29'
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
                                'configType': {
                                    'name': 'Any'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.1'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.2'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.2'
                            },
                            {
                                'name': 'Dict.1'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Any'
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
                                'configType': {
                                    'name': 'Dict.3'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.4'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'NoConfigPipeline.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.125'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default'
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
                                'configType': {
                                    'name': 'Dict.125'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'NoConfigPipeline.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.125'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'NoConfigPipeline.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'NoConfigPipeline.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'NoConfigPipeline.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'NoConfigPipeline.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'NoConfigPipeline.SolidConfig.ReturnHello'
                            },
                            {
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'Dict.125'
                            },
                            {
                                'name': 'NoConfigPipeline.ExpectationsConfig'
                            },
                            {
                                'name': 'List.NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'NoConfigPipeline.ContextConfig'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'NoConfigPipeline.ExecutionConfig'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'NoConfigPipeline.SolidsConfigDictionary'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'Any.MaterializationSchema'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
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
                                'configType': {
                                    'name': 'List.NoConfigPipeline.ReturnHello.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'List.NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
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
                                'configType': {
                                    'name': 'NoConfigPipeline.SolidConfig.ReturnHello'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'return_hello'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'NoConfigPipeline.SolidConfig.ReturnHello'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'List.NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
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
                                'configType': {
                                    'name': 'Any'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.1'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.2'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.2'
                            },
                            {
                                'name': 'Dict.1'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Any'
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
                                'configType': {
                                    'name': 'Dict.3'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.4'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.5'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.6'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'Dict.5'
                            },
                            {
                                'name': 'Dict.6'
                            },
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Dict.7'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.8'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.7'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Int'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.13'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.14'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.13'
                            },
                            {
                                'name': 'Dict.14'
                            },
                            {
                                'name': 'Int'
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
                                'configType': {
                                    'name': 'Dict.15'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.16'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.126'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.126'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.126'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'ScalarOutputPipeline.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'ScalarOutputPipeline.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'ScalarOutputPipeline.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'ScalarOutputPipeline.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Dict.126'
                            },
                            {
                                'name': 'Int.MaterializationSchema'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnBool'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'name': 'Bool.MaterializationSchema'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnAny'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'Dict.21'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextConfig'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Dict.22'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnStr'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ExpectationsConfig'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'String.MaterializationSchema'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ExecutionConfig'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnInt'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'Dict.7'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'Any.MaterializationSchema'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
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
                                'configType': {
                                    'name': 'Bool.MaterializationSchema'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Bool.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.7'
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
                                'configType': {
                                    'name': 'Int.MaterializationSchema'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Int.MaterializationSchema'
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
                                'configType': {
                                    'name': 'String.MaterializationSchema'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.22'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.21'
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
                                'configType': {
                                    'name': 'List.ScalarOutputPipeline.ReturnAny.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnAny.Outputs'
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
                                'configType': {
                                    'name': 'List.ScalarOutputPipeline.ReturnBool.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'name': 'Bool.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.7'
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
                                'configType': {
                                    'name': 'List.ScalarOutputPipeline.ReturnInt.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Int.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnInt.Outputs'
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
                                'configType': {
                                    'name': 'List.ScalarOutputPipeline.ReturnStr.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.22'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.21'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnStr.Outputs'
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
                                'configType': {
                                    'name': 'ScalarOutputPipeline.SolidConfig.ReturnStr'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'return_str'
                            },
                            {
                                'configType': {
                                    'name': 'ScalarOutputPipeline.SolidConfig.ReturnInt'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'return_int'
                            },
                            {
                                'configType': {
                                    'name': 'ScalarOutputPipeline.SolidConfig.ReturnBool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'return_bool'
                            },
                            {
                                'configType': {
                                    'name': 'ScalarOutputPipeline.SolidConfig.ReturnAny'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'return_any'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'Dict.7'
                            },
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnBool'
                            },
                            {
                                'name': 'Int.MaterializationSchema'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnInt'
                            },
                            {
                                'name': 'Bool.MaterializationSchema'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnAny'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'Dict.21'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'Dict.22'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnStr'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'String.MaterializationSchema'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnInt.Outputs'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.19'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.20'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.20'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.19'
                            },
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Dict.21'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.22'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.21'
                            },
                            {
                                'name': 'Dict.22'
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
                                'configType': {
                                    'name': 'Any'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'value'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.1'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.2'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.2'
                            },
                            {
                                'name': 'Dict.1'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Any'
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
                                'configType': {
                                    'name': 'Dict.3'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'json'
                            },
                            {
                                'configType': {
                                    'name': 'Dict.4'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'pickle'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'String'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'log_level'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'String'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'Path'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'path'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Path'
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
                                'configType': {
                                    'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'default'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.127'
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
                                'configType': {
                                    'name': 'Dict.127'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default.Resources'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'resources'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.127'
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
                                'configType': {
                                    'name': 'PipelineWithEnumConfig.ContextConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'context'
                            },
                            {
                                'configType': {
                                    'name': 'PipelineWithEnumConfig.SolidsConfigDictionary'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'solids'
                            },
                            {
                                'configType': {
                                    'name': 'PipelineWithEnumConfig.ExpectationsConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'expectations'
                            },
                            {
                                'configType': {
                                    'name': 'PipelineWithEnumConfig.ExecutionConfig'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'execution'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'List.PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'Dict.127'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.SolidConfig.TakesAnEnum'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ExpectationsConfig'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ContextConfig'
                            },
                            {
                                'name': 'TestEnum'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ExecutionConfig'
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
                                'configType': {
                                    'name': 'Bool'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'evaluate'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Bool'
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
                                'configType': {
                                    'name': 'TestEnum'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'config'
                            },
                            {
                                'configType': {
                                    'name': 'List.PipelineWithEnumConfig.TakesAnEnum.Outputs'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'outputs'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'List.PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'TestEnum'
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
                                'configType': {
                                    'name': 'PipelineWithEnumConfig.SolidConfig.TakesAnEnum'
                                },
                                'description': None,
                                'isOptional': False,
                                'name': 'takes_an_enum'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.SolidConfig.TakesAnEnum'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'List.PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'TestEnum'
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
                                'configType': {
                                    'name': 'Any.MaterializationSchema'
                                },
                                'description': None,
                                'isOptional': True,
                                'name': 'result'
                            }
                        ],
                        'innerTypes': [
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
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
