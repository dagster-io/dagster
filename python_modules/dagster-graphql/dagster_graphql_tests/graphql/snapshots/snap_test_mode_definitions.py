# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_query_multi_mode 1'] = {
    'pipeline': {
        'configTypes': [
            {
                'key': 'Any'
            },
            {
                'key': 'Any.InputSchema'
            },
            {
                'key': 'Any.MaterializationSchema'
            },
            {
                'key': 'Bool'
            },
            {
                'key': 'Bool.InputSchema'
            },
            {
                'key': 'Bool.MaterializationSchema'
            },
            {
                'key': 'Dict.1'
            },
            {
                'key': 'Dict.10'
            },
            {
                'key': 'Dict.11'
            },
            {
                'key': 'Dict.12'
            },
            {
                'key': 'Dict.13'
            },
            {
                'key': 'Dict.14'
            },
            {
                'key': 'Dict.15'
            },
            {
                'key': 'Dict.16'
            },
            {
                'key': 'Dict.17'
            },
            {
                'key': 'Dict.18'
            },
            {
                'key': 'Dict.19'
            },
            {
                'key': 'Dict.2'
            },
            {
                'key': 'Dict.20'
            },
            {
                'key': 'Dict.21'
            },
            {
                'key': 'Dict.22'
            },
            {
                'key': 'Dict.3'
            },
            {
                'key': 'Dict.4'
            },
            {
                'key': 'Dict.457'
            },
            {
                'key': 'Dict.5'
            },
            {
                'key': 'Dict.6'
            },
            {
                'key': 'Dict.7'
            },
            {
                'key': 'Dict.8'
            },
            {
                'key': 'Dict.9'
            },
            {
                'key': 'Float'
            },
            {
                'key': 'Float.InputSchema'
            },
            {
                'key': 'Float.MaterializationSchema'
            },
            {
                'key': 'Int'
            },
            {
                'key': 'Int.InputSchema'
            },
            {
                'key': 'Int.MaterializationSchema'
            },
            {
                'key': 'MultiModeWithResources.ApplyToThree.Outputs'
            },
            {
                'key': 'MultiModeWithResources.ExecutionConfig'
            },
            {
                'key': 'MultiModeWithResources.ExpectationsConfig'
            },
            {
                'key': 'MultiModeWithResources.Mode.AddMode.Environment'
            },
            {
                'key': 'MultiModeWithResources.Mode.AddMode.Resources'
            },
            {
                'key': 'MultiModeWithResources.Mode.AddMode.Resources.op'
            },
            {
                'key': 'MultiModeWithResources.SolidConfig.ApplyToThree'
            },
            {
                'key': 'MultiModeWithResources.SolidsConfigDictionary'
            },
            {
                'key': 'MultiModeWithResources.StorageConfig'
            },
            {
                'key': 'MultiModeWithResources.StorageConfig.Files'
            },
            {
                'key': 'MultiModeWithResources.StorageConfig.InMem'
            },
            {
                'key': 'MultiModeWithResources.StorageConfig.S3'
            },
            {
                'key': 'Path'
            },
            {
                'key': 'Path.MaterializationSchema'
            },
            {
                'key': 'String'
            },
            {
                'key': 'String.InputSchema'
            },
            {
                'key': 'String.MaterializationSchema'
            },
            {
                'key': 'log_level'
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
                'key': 'Any'
            },
            {
                'key': 'Any.InputSchema'
            },
            {
                'key': 'Any.MaterializationSchema'
            },
            {
                'key': 'Bool'
            },
            {
                'key': 'Bool.InputSchema'
            },
            {
                'key': 'Bool.MaterializationSchema'
            },
            {
                'key': 'Dict.1'
            },
            {
                'key': 'Dict.10'
            },
            {
                'key': 'Dict.11'
            },
            {
                'key': 'Dict.12'
            },
            {
                'key': 'Dict.13'
            },
            {
                'key': 'Dict.14'
            },
            {
                'key': 'Dict.15'
            },
            {
                'key': 'Dict.16'
            },
            {
                'key': 'Dict.17'
            },
            {
                'key': 'Dict.18'
            },
            {
                'key': 'Dict.19'
            },
            {
                'key': 'Dict.2'
            },
            {
                'key': 'Dict.20'
            },
            {
                'key': 'Dict.21'
            },
            {
                'key': 'Dict.22'
            },
            {
                'key': 'Dict.3'
            },
            {
                'key': 'Dict.4'
            },
            {
                'key': 'Dict.459'
            },
            {
                'key': 'Dict.5'
            },
            {
                'key': 'Dict.6'
            },
            {
                'key': 'Dict.7'
            },
            {
                'key': 'Dict.8'
            },
            {
                'key': 'Dict.9'
            },
            {
                'key': 'Float'
            },
            {
                'key': 'Float.InputSchema'
            },
            {
                'key': 'Float.MaterializationSchema'
            },
            {
                'key': 'Int'
            },
            {
                'key': 'Int.InputSchema'
            },
            {
                'key': 'Int.MaterializationSchema'
            },
            {
                'key': 'MultiModeWithResources.ApplyToThree.Outputs'
            },
            {
                'key': 'MultiModeWithResources.ExecutionConfig'
            },
            {
                'key': 'MultiModeWithResources.ExpectationsConfig'
            },
            {
                'key': 'MultiModeWithResources.Mode.AddMode.Environment'
            },
            {
                'key': 'MultiModeWithResources.Mode.AddMode.Resources'
            },
            {
                'key': 'MultiModeWithResources.Mode.AddMode.Resources.op'
            },
            {
                'key': 'MultiModeWithResources.SolidConfig.ApplyToThree'
            },
            {
                'key': 'MultiModeWithResources.SolidsConfigDictionary'
            },
            {
                'key': 'MultiModeWithResources.StorageConfig'
            },
            {
                'key': 'MultiModeWithResources.StorageConfig.Files'
            },
            {
                'key': 'MultiModeWithResources.StorageConfig.InMem'
            },
            {
                'key': 'MultiModeWithResources.StorageConfig.S3'
            },
            {
                'key': 'Path'
            },
            {
                'key': 'Path.MaterializationSchema'
            },
            {
                'key': 'String'
            },
            {
                'key': 'String.InputSchema'
            },
            {
                'key': 'String.MaterializationSchema'
            },
            {
                'key': 'log_level'
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
