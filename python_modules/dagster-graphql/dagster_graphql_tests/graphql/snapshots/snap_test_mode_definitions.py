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
                'name': 'Any.InputSchema'
            },
            {
                'name': 'Any.MaterializationSchema'
            },
            {
                'name': 'Bool'
            },
            {
                'name': 'Bool.InputSchema'
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
                'name': 'Float'
            },
            {
                'name': 'Float.InputSchema'
            },
            {
                'name': 'Float.MaterializationSchema'
            },
            {
                'name': 'Int'
            },
            {
                'name': 'Int.InputSchema'
            },
            {
                'name': 'Int.MaterializationSchema'
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
                'name': 'MultiModeWithResources.Mode.AddMode.Environment'
            },
            {
                'name': 'MultiModeWithResources.Mode.AddMode.Resources'
            },
            {
                'name': 'MultiModeWithResources.Mode.AddMode.Resources.op'
            },
            {
                'name': 'MultiModeWithResources.SolidConfig.ApplyToThree'
            },
            {
                'name': 'MultiModeWithResources.SolidsConfigDictionary'
            },
            {
                'name': 'MultiModeWithResources.StorageConfig'
            },
            {
                'name': 'MultiModeWithResources.StorageConfig.Files'
            },
            {
                'name': 'MultiModeWithResources.StorageConfig.InMem'
            },
            {
                'name': 'MultiModeWithResources.StorageConfig.S3'
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
                'name': 'String.InputSchema'
            },
            {
                'name': 'String.MaterializationSchema'
            },
            {
                'name': 'log_level'
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
                        'name': 'MultiModeWithResources.StorageConfig'
                    }
                }
            ],
            'name': 'MultiModeWithResources.Mode.AddMode.Environment'
        },
        'modes': [
            {
                'description': 'Mode that adds things',
                'name': 'add_mode',
                'resources': [
                    {
                        'config': {
                            'configType': {
                                'name': 'Int'
                            }
                        },
                        'name': 'op'
                    }
                ]
            },
            {
                'description': 'Mode that multiplies things',
                'name': 'mult_mode',
                'resources': [
                    {
                        'config': {
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
                'name': 'double_adder',
                'resources': [
                    {
                        'config': {
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
            }
        ]
    }
}

snapshots['test_query_multi_mode 2'] = {
    'pipeline': {
        'configTypes': [
            {
                'name': 'Any'
            },
            {
                'name': 'Any.InputSchema'
            },
            {
                'name': 'Any.MaterializationSchema'
            },
            {
                'name': 'Bool'
            },
            {
                'name': 'Bool.InputSchema'
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
                'name': 'Float'
            },
            {
                'name': 'Float.InputSchema'
            },
            {
                'name': 'Float.MaterializationSchema'
            },
            {
                'name': 'Int'
            },
            {
                'name': 'Int.InputSchema'
            },
            {
                'name': 'Int.MaterializationSchema'
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
                'name': 'MultiModeWithResources.Mode.AddMode.Environment'
            },
            {
                'name': 'MultiModeWithResources.Mode.AddMode.Resources'
            },
            {
                'name': 'MultiModeWithResources.Mode.AddMode.Resources.op'
            },
            {
                'name': 'MultiModeWithResources.SolidConfig.ApplyToThree'
            },
            {
                'name': 'MultiModeWithResources.SolidsConfigDictionary'
            },
            {
                'name': 'MultiModeWithResources.StorageConfig'
            },
            {
                'name': 'MultiModeWithResources.StorageConfig.Files'
            },
            {
                'name': 'MultiModeWithResources.StorageConfig.InMem'
            },
            {
                'name': 'MultiModeWithResources.StorageConfig.S3'
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
                'name': 'String.InputSchema'
            },
            {
                'name': 'String.MaterializationSchema'
            },
            {
                'name': 'log_level'
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
                        'name': 'MultiModeWithResources.StorageConfig'
                    }
                }
            ],
            'name': 'MultiModeWithResources.Mode.AddMode.Environment'
        },
        'modes': [
            {
                'description': 'Mode that adds things',
                'name': 'add_mode',
                'resources': [
                    {
                        'config': {
                            'configType': {
                                'name': 'Int'
                            }
                        },
                        'name': 'op'
                    }
                ]
            },
            {
                'description': 'Mode that multiplies things',
                'name': 'mult_mode',
                'resources': [
                    {
                        'config': {
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
                'name': 'double_adder',
                'resources': [
                    {
                        'config': {
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
            }
        ]
    }
}
