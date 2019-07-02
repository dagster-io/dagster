# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_successful_enviroment_schema 1'] = {
    'environmentSchemaOrError': {
        '__typename': 'EnvironmentSchema',
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
        'rootEnvironmentType': {
            'name': 'MultiModeWithResources.Mode.AddMode.Environment'
        }
    }
}

snapshots['test_success_config_type_fetch 1'] = {
    'environmentSchemaOrError': {
        '__typename': 'EnvironmentSchema',
        'configTypeOrError': {
            '__typename': 'CompositeConfigType',
            'name': 'MultiModeWithResources.Mode.AddMode.Environment'
        }
    }
}

snapshots['test_success_config_type_not_found 1'] = {
    'environmentSchemaOrError': {
        '__typename': 'EnvironmentSchema',
        'configTypeOrError': {
            '__typename': 'ConfigTypeNotFoundError'
        }
    }
}

snapshots['test_basic_valid_config_on_environment_schema 1'] = {
    'environmentSchemaOrError': {
        'isEnvironmentConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipeline': {
                'name': 'csv_hello_world'
            }
        }
    }
}

snapshots['test_basic_invalid_config_on_environment_schema 1'] = {
    'environmentSchemaOrError': {
        'isEnvironmentConfigValid': {
            '__typename': 'PipelineConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Field "nope" is not defined at document config root. Expected: "{ execution?: CsvHelloWorld.ExecutionConfig expectations?: CsvHelloWorld.ExpectationsConfig loggers?: CsvHelloWorld.LoggerConfig resources?: CsvHelloWorld.Mode.Default.Resources solids: CsvHelloWorld.SolidsConfigDictionary storage?: CsvHelloWorld.Default.StorageConfig }"',
                    'reason': 'FIELD_NOT_DEFINED',
                    'stack': {
                        'entries': [
                        ]
                    }
                },
                {
                    '__typename': 'MissingFieldConfigError',
                    'field': {
                        'name': 'solids'
                    },
                    'message': 'Missing required field "solids" at document config root. Available Fields: "[\'execution\', \'expectations\', \'loggers\', \'resources\', \'solids\', \'storage\']".',
                    'reason': 'MISSING_REQUIRED_FIELD',
                    'stack': {
                        'entries': [
                        ]
                    }
                }
            ],
            'pipeline': {
                'name': 'csv_hello_world'
            }
        }
    }
}
