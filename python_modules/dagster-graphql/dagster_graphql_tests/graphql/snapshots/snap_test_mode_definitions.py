# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_query_multi_mode 1'] = {
    'pipeline': {
        'configTypes': [
            {
                'name': 'Any'
            },
            {
                'name': 'Any.InputHydrationConfig'
            },
            {
                'name': 'Any.MaterializationSchema'
            },
            {
                'name': 'Bool'
            },
            {
                'name': 'Bool.InputHydrationConfig'
            },
            {
                'name': 'Bool.MaterializationSchema'
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': None
            },
            {
                'name': 'Float'
            },
            {
                'name': 'Float.InputHydrationConfig'
            },
            {
                'name': 'Float.MaterializationSchema'
            },
            {
                'name': 'Int'
            },
            {
                'name': 'Int.InputHydrationConfig'
            },
            {
                'name': 'Int.MaterializationSchema'
            },
            {
                'name': 'MultiModeWithResources.AddMode.StorageConfig'
            },
            {
                'name': 'MultiModeWithResources.AddMode.StorageConfig.Filesystem'
            },
            {
                'name': 'MultiModeWithResources.AddMode.StorageConfig.InMemory'
            },
            {
                'name': 'MultiModeWithResources.ApplyToThree.Outputs'
            },
            {
                'name': 'MultiModeWithResources.ExecutionConfig'
            },
            {
                'name': 'MultiModeWithResources.ExpectationsConfig'
            },
            {
                'name': 'MultiModeWithResources.LoggerConfig'
            },
            {
                'name': 'MultiModeWithResources.LoggerConfig.Console'
            },
            {
                'name': 'MultiModeWithResources.Mode.AddMode.Environment'
            },
            {
                'name': 'MultiModeWithResources.Mode.AddMode.Resources'
            },
            {
                'name': 'MultiModeWithResources.Mode.AddMode.Resources.Op'
            },
            {
                'name': 'MultiModeWithResources.SolidConfig.ApplyToThree'
            },
            {
                'name': 'MultiModeWithResources.SolidsConfigDictionary'
            },
            {
                'name': 'Path'
            },
            {
                'name': 'Path.MaterializationSchema'
            },
            {
                'name': 'String'
            },
            {
                'name': 'String.InputHydrationConfig'
            },
            {
                'name': 'String.MaterializationSchema'
            }
        ],
        'environmentType': {
            'fields': [
                {
                    'configType': {
                        'name': 'MultiModeWithResources.ExecutionConfig'
                    }
                },
                {
                    'configType': {
                        'name': 'MultiModeWithResources.ExpectationsConfig'
                    }
                },
                {
                    'configType': {
                        'name': 'MultiModeWithResources.LoggerConfig'
                    }
                },
                {
                    'configType': {
                        'name': 'MultiModeWithResources.Mode.AddMode.Resources'
                    }
                },
                {
                    'configType': {
                        'name': 'MultiModeWithResources.SolidsConfigDictionary'
                    }
                },
                {
                    'configType': {
                        'name': 'MultiModeWithResources.AddMode.StorageConfig'
                    }
                }
            ],
            'name': 'MultiModeWithResources.Mode.AddMode.Environment'
        },
        'modes': [
            {
                'description': 'Mode that adds things',
                'loggers': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'log_level'
                                    },
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'name'
                                    }
                                ],
                                'name': None
                            }
                        },
                        'name': 'console'
                    }
                ],
                'name': 'add_mode',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'name': 'Int'
                            }
                        },
                        'name': 'op'
                    }
                ]
            },
            {
                'description': 'Mode that adds two numbers to thing',
                'loggers': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'log_level'
                                    },
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'name'
                                    }
                                ],
                                'name': None
                            }
                        },
                        'name': 'console'
                    }
                ],
                'name': 'double_adder',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'name': 'Int'
                                        },
                                        'name': 'num_one'
                                    },
                                    {
                                        'configType': {
                                            'name': 'Int'
                                        },
                                        'name': 'num_two'
                                    }
                                ],
                                'name': None
                            }
                        },
                        'name': 'op'
                    }
                ]
            },
            {
                'description': 'Mode that multiplies things',
                'loggers': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'log_level'
                                    },
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'name'
                                    }
                                ],
                                'name': None
                            }
                        },
                        'name': 'console'
                    }
                ],
                'name': 'mult_mode',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'name': 'Int'
                            }
                        },
                        'name': 'op'
                    }
                ]
            }
        ],
        'presets': [
            {
                'mode': 'add_mode',
                'name': 'add'
            }
        ]
    }
}
