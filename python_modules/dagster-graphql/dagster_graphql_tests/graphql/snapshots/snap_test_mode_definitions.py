# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_query_multi_mode 1'] = {
    'environmentSchemaOrError': {
        'allConfigTypes': [
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
                'name': 'MultiModeWithResources.AddMode.ExecutionConfig'
            },
            {
                'name': 'MultiModeWithResources.AddMode.ExecutionConfig.InProcess'
            },
            {
                'name': 'MultiModeWithResources.AddMode.ExecutionConfig.Multiprocess'
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
        'rootEnvironmentType': {
            'fields': [
                {
                    'configType': {
                        'name': 'MultiModeWithResources.AddMode.ExecutionConfig'
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
        }
    }
}
