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
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne.Resources'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources'
                            },
                            {
                                'name': 'Dict.115'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo.Resources'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ContextConfig'
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
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne.Resources'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne'
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
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne.Resources'
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
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo'
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
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo.Resources'
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
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources'
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
                                'name': 'Int'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources'
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
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
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
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne.Resources'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources'
                            },
                            {
                                'name': 'ContextConfigPipeline.ExpectationsConfig'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextConfig'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextOne'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextWithResources.Resources.resource_one'
                            },
                            {
                                'name': 'ContextConfigPipeline.ExecutionConfig'
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
                                'name': 'ContextConfigPipeline.SolidsConfigDictionary'
                            },
                            {
                                'name': 'ContextConfigPipeline.ContextDefinitionConfig.ContextTwo.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.ExpectationsConfig'
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
                        'isSystemGenerated': True,
                        'name': 'ContextConfigPipeline.SolidsConfigDictionary'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.115'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Int'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.116'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.117'
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
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.117'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedConfig.ContextConfig'
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
                                'name': 'Dict.117'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'MoreComplicatedConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.117'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ContextConfig'
                            },
                            {
                                'name': 'Bool'
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
                                'name': 'MoreComplicatedConfig.SolidsConfigDictionary'
                            },
                            {
                                'name': 'MoreComplicatedConfig.SolidConfig.ASolidWithThreeFieldConfig'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedConfig.ExecutionConfig'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedConfig.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedConfig.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedConfig.ExpectationsConfig'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.116'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedConfig.SolidConfig.ASolidWithThreeFieldConfig'
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
                                'name': 'MoreComplicatedConfig.SolidConfig.ASolidWithThreeFieldConfig'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.116'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedConfig.SolidsConfigDictionary'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                                'name': 'List.Nullable.Int'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'Nullable.Int'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Dict.118'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.119'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.120'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Int'
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
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.120'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedNestedConfig.ContextConfig'
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
                                'name': 'Dict.120'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'MoreComplicatedNestedConfig.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Dict.119'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ExecutionConfig'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
                            },
                            {
                                'name': 'Dict.118'
                            },
                            {
                                'name': 'Bool'
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
                                'name': 'Int'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextConfig'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ExpectationsConfig'
                            },
                            {
                                'name': 'MoreComplicatedNestedConfig.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedNestedConfig.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedNestedConfig.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedNestedConfig.ExpectationsConfig'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.119'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
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
                                'name': 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
                            },
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
                            },
                            {
                                'name': 'Dict.119'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'MoreComplicatedNestedConfig.SolidsConfigDictionary'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.121'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Dict.23'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.24'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.25'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Dict.27'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.28'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.29'
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
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Dict.121'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.ContextConfig'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.121'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'PandasHelloWorld.ExecutionConfig'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'PandasHelloWorld.ContextConfig'
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
                                'name': 'PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'PandasHelloWorld.SolidConfig.SumSqSolid'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.28'
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
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'PandasHelloWorld.ExpectationsConfig'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.ExpectationsConfig'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Inputs'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.SolidConfig.SumSolid'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSqSolid.Outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.SolidConfig.SumSqSolid'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'PandasHelloWorld.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Inputs'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSolid.Outputs'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorld.SolidConfig.SumSqSolid'
                            },
                            {
                                'name': 'List.PandasHelloWorld.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.SolidsConfigDictionary'
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
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.SumSolid.Inputs'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.SumSolid.Outputs'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorld.SumSqSolid.Outputs'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Path'
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
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False,
                        'name': 'Selector.26'
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
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False,
                        'name': 'Selector.30'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.122'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Dict.23'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.24'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.25'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Dict.27'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.28'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.29'
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
                                'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.122'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.ContextConfig'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.122'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.ExpectationsConfig'
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
                                'name': 'Bool'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'Dict.28'
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
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Selector.30'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.ExpectationsConfig'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Inputs'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'List.PandasHelloWorldTwo.SumSolid.Outputs'
                            },
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
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.SolidConfig.SumSolid'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Inputs'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'List.PandasHelloWorldTwo.SumSolid.Outputs'
                            },
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
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldTwo.SolidConfig.SumSolid'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.SolidsConfigDictionary'
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
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.SumSolid.Inputs'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldTwo.SumSolid.Outputs'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Path'
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
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False,
                        'name': 'Selector.26'
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
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False,
                        'name': 'Selector.30'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.123'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Int'
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
                                'name': 'String'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithList.ContextConfig'
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
                                'name': 'Dict.123'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithList.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'PipelineWithList.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'Dict.123'
                            },
                            {
                                'name': 'PipelineWithList.ContextConfig'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'PipelineWithList.ExpectationsConfig'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'PipelineWithList.SolidsConfigDictionary'
                            },
                            {
                                'name': 'List.Int'
                            },
                            {
                                'name': 'PipelineWithList.ExecutionConfig'
                            },
                            {
                                'name': 'PipelineWithList.SolidConfig.SolidWithList'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PipelineWithList.ContextDefinitionConfig.Default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithList.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'PipelineWithList.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'PipelineWithList.ExpectationsConfig'
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
                                'name': 'Int'
                            },
                            {
                                'name': 'List.Int'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithList.SolidConfig.SolidWithList'
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
                                'name': 'PipelineWithList.SolidConfig.SolidWithList'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'List.Int'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithList.SolidsConfigDictionary'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.124'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Dict.23'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.24'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.25'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Dict.27'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.28'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.29'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.124'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.ContextConfig'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.124'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'PandasHelloWorldDfInput.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSolid.Outputs'
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
                                'name': 'Bool'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ExecutionConfig'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.ContextConfig'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Inputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.ExpectationsConfig'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.28'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.25'
                            },
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
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Inputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.SolidConfig.SumSolid'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.SolidConfig.SumSqSolid'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SolidConfig.SumSolid'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SolidConfig.SumSqSolid'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'PandasHelloWorldDfInput.SumSolid.Inputs'
                            },
                            {
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSolid.Outputs'
                            },
                            {
                                'name': 'List.PandasHelloWorldDfInput.SumSqSolid.Outputs'
                            },
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
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.SolidsConfigDictionary'
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
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Selector.30'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.SumSolid.Inputs'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.SumSolid.Outputs'
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
                                'name': 'Selector.26'
                            },
                            {
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PandasHelloWorldDfInput.SumSqSolid.Outputs'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Path'
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
                                'name': 'Dict.23'
                            },
                            {
                                'name': 'Dict.24'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.25'
                            },
                            {
                                'name': 'String'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False,
                        'name': 'Selector.26'
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
                                'name': 'Dict.29'
                            },
                            {
                                'name': 'Dict.27'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.28'
                            }
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': False,
                        'name': 'Selector.30'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'isSystemGenerated': False,
                        'name': 'Any'
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
                                'name': 'Any'
                            },
                            {
                                'name': 'Dict.2'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.1'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Any.InputSchema'
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
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Any.MaterializationSchema'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.1'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.125'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.2'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.3'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.4'
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
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.125'
                            },
                            {
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.ContextConfig'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.125'
                            },
                            {
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'NoConfigPipeline.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'NoConfigPipeline.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'NoConfigPipeline.SolidConfig.ReturnHello'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'Dict.125'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'List.NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'NoConfigPipeline.ExpectationsConfig'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'NoConfigPipeline.ContextConfig'
                            },
                            {
                                'name': 'NoConfigPipeline.ExecutionConfig'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.ExpectationsConfig'
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
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.ReturnHello.Outputs'
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
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'List.NoConfigPipeline.ReturnHello.Outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.SolidConfig.ReturnHello'
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
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'NoConfigPipeline.SolidConfig.ReturnHello'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'NoConfigPipeline.ReturnHello.Outputs'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'List.NoConfigPipeline.ReturnHello.Outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'NoConfigPipeline.SolidsConfigDictionary'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Path'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'isSystemGenerated': False,
                        'name': 'Any'
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
                                'name': 'Any'
                            },
                            {
                                'name': 'Dict.2'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.1'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Any.InputSchema'
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
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Any.MaterializationSchema'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                                'name': 'Dict.5'
                            },
                            {
                                'name': 'Dict.6'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Bool.InputSchema'
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
                                'name': 'Dict.7'
                            },
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Bool.MaterializationSchema'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.1'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.126'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.13'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.14'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.15'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.16'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.19'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.2'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.20'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.21'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.22'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.3'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.4'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.5'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.6'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.7'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.8'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Int'
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
                                'name': 'Dict.13'
                            },
                            {
                                'name': 'Dict.14'
                            },
                            {
                                'name': 'Int'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Int.InputSchema'
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
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Int.MaterializationSchema'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Path'
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
                                'name': 'String'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.126'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ContextConfig'
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
                                'name': 'String'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.126'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnInt'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Int.MaterializationSchema'
                            },
                            {
                                'name': 'Bool.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.126'
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
                                'name': 'Dict.21'
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
                                'name': 'List.ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'Dict.22'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ContextConfig'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidsConfigDictionary'
                            },
                            {
                                'name': 'String.MaterializationSchema'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnStr'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ExpectationsConfig'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ExecutionConfig'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'Dict.7'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ExpectationsConfig'
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
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ReturnAny.Outputs'
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
                                'name': 'Path'
                            },
                            {
                                'name': 'Bool.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Dict.7'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ReturnBool.Outputs'
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
                                'name': 'Int.MaterializationSchema'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.16'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ReturnInt.Outputs'
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
                                'name': 'String.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.21'
                            },
                            {
                                'name': 'Dict.22'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.ReturnStr.Outputs'
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
                                'name': 'ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.SolidConfig.ReturnAny'
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
                                'name': 'Dict.7'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnBool.Outputs'
                            },
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Bool.MaterializationSchema'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.SolidConfig.ReturnBool'
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
                                'name': 'ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'Int.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.SolidConfig.ReturnInt'
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
                                'name': 'ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnStr.Outputs'
                            },
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
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.SolidConfig.ReturnStr'
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
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnInt'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'Dict.16'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnInt.Outputs'
                            },
                            {
                                'name': 'Dict.8'
                            },
                            {
                                'name': 'Int.MaterializationSchema'
                            },
                            {
                                'name': 'Bool.MaterializationSchema'
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
                                'name': 'Dict.21'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnAny'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnAny.Outputs'
                            },
                            {
                                'name': 'Dict.22'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String.MaterializationSchema'
                            },
                            {
                                'name': 'ScalarOutputPipeline.SolidConfig.ReturnStr'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'List.ScalarOutputPipeline.ReturnStr.Outputs'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.15'
                            },
                            {
                                'name': 'Dict.7'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'ScalarOutputPipeline.SolidsConfigDictionary'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                                'name': 'Dict.19'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.20'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'String.InputSchema'
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
                                'name': 'Dict.21'
                            },
                            {
                                'name': 'Dict.22'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'String.MaterializationSchema'
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
                        'isSystemGenerated': False,
                        'name': 'Any'
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
                                'name': 'Any'
                            },
                            {
                                'name': 'Dict.2'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'Dict.1'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Any.InputSchema'
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
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'Any.MaterializationSchema'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Bool'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.1'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.127'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.2'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.3'
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
                        'isSystemGenerated': False,
                        'name': 'Dict.4'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'Path'
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
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'Dict.127'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': True,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.ContextConfig'
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
                                'name': 'String'
                            },
                            {
                                'name': 'Dict.127'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default.Resources'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default'
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
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default.Resources'
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
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default'
                            },
                            {
                                'name': 'List.PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ContextConfig'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ExpectationsConfig'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ExecutionConfig'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.ContextDefinitionConfig.Default.Resources'
                            },
                            {
                                'name': 'TestEnum'
                            },
                            {
                                'name': 'Bool'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.SolidsConfigDictionary'
                            },
                            {
                                'name': 'Dict.127'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'String'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.SolidConfig.TakesAnEnum'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.Environment'
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
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.ExecutionConfig'
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
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.ExpectationsConfig'
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
                                'name': 'List.PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'TestEnum'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.SolidConfig.TakesAnEnum'
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
                                'name': 'List.PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'TestEnum'
                            },
                            {
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Path'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.SolidConfig.TakesAnEnum'
                            },
                            {
                                'name': 'PipelineWithEnumConfig.TakesAnEnum.Outputs'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.SolidsConfigDictionary'
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
                                'name': 'Any.MaterializationSchema'
                            },
                            {
                                'name': 'Dict.3'
                            },
                            {
                                'name': 'Dict.4'
                            },
                            {
                                'name': 'Path'
                            }
                        ],
                        'isBuiltin': False,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': True,
                        'name': 'PipelineWithEnumConfig.TakesAnEnum.Outputs'
                    },
                    {
                        'description': '',
                        'innerTypes': [
                        ],
                        'isBuiltin': True,
                        'isList': False,
                        'isNullable': False,
                        'isSelector': False,
                        'isSystemGenerated': False,
                        'name': 'String'
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
                        'name': 'TestEnum',
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
