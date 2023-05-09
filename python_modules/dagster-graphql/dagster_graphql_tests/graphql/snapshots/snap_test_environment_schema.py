# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'RunConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } loggers?: { console?: { config?: { log_level?: String name?: String } } } ops: { sum_op: { config?: Any inputs: { num: String } } sum_sq_op?: { config?: Any } } resources?: { io_manager?: { config?: Any } } }".',
                    'reason': 'FIELD_NOT_DEFINED',
                    'stack': {
                        'entries': [
                        ]
                    }
                },
                {
                    '__typename': 'MissingFieldConfigError',
                    'field': {
                        'name': 'ops'
                    },
                    'message': 'Missing required config entry "ops" at the root. Sample config for missing entry: {\'ops\': {\'sum_op\': {\'inputs\': {\'num\': \'...\'}}}}',
                    'reason': 'MISSING_REQUIRED_FIELD',
                    'stack': {
                        'entries': [
                        ]
                    }
                }
            ],
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[non_launchable_sqlite_instance_lazy_repository] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'RunConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } loggers?: { console?: { config?: { log_level?: String name?: String } } } ops: { sum_op: { config?: Any inputs: { num: String } } sum_sq_op?: { config?: Any } } resources?: { io_manager?: { config?: Any } } }".',
                    'reason': 'FIELD_NOT_DEFINED',
                    'stack': {
                        'entries': [
                        ]
                    }
                },
                {
                    '__typename': 'MissingFieldConfigError',
                    'field': {
                        'name': 'ops'
                    },
                    'message': 'Missing required config entry "ops" at the root. Sample config for missing entry: {\'ops\': {\'sum_op\': {\'inputs\': {\'num\': \'...\'}}}}',
                    'reason': 'MISSING_REQUIRED_FIELD',
                    'stack': {
                        'entries': [
                        ]
                    }
                }
            ],
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'RunConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } loggers?: { console?: { config?: { log_level?: String name?: String } } } ops: { sum_op: { config?: Any inputs: { num: String } } sum_sq_op?: { config?: Any } } resources?: { io_manager?: { config?: Any } } }".',
                    'reason': 'FIELD_NOT_DEFINED',
                    'stack': {
                        'entries': [
                        ]
                    }
                },
                {
                    '__typename': 'MissingFieldConfigError',
                    'field': {
                        'name': 'ops'
                    },
                    'message': 'Missing required config entry "ops" at the root. Sample config for missing entry: {\'ops\': {\'sum_op\': {\'inputs\': {\'num\': \'...\'}}}}',
                    'reason': 'MISSING_REQUIRED_FIELD',
                    'stack': {
                        'entries': [
                        ]
                    }
                }
            ],
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[non_launchable_sqlite_instance_multi_location] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'RunConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } loggers?: { console?: { config?: { log_level?: String name?: String } } } ops: { sum_op: { config?: Any inputs: { num: String } } sum_sq_op?: { config?: Any } } resources?: { io_manager?: { config?: Any } } }".',
                    'reason': 'FIELD_NOT_DEFINED',
                    'stack': {
                        'entries': [
                        ]
                    }
                },
                {
                    '__typename': 'MissingFieldConfigError',
                    'field': {
                        'name': 'ops'
                    },
                    'message': 'Missing required config entry "ops" at the root. Sample config for missing entry: {\'ops\': {\'sum_op\': {\'inputs\': {\'num\': \'...\'}}}}',
                    'reason': 'MISSING_REQUIRED_FIELD',
                    'stack': {
                        'entries': [
                        ]
                    }
                }
            ],
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[non_launchable_sqlite_instance_lazy_repository] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[non_launchable_sqlite_instance_multi_location] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_full_yaml[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        '__typename': 'RunConfigSchema',
        'rootDefaultYaml': '''execution:
  config:
    retries:
      enabled: {}
loggers: {}
ops:
  sum_op:
    inputs: {}
  sum_sq_op: {}
resources:
  io_manager: {}
'''
    }
}

snapshots['TestEnvironmentSchema.test_full_yaml[non_launchable_sqlite_instance_lazy_repository] 1'] = {
    'runConfigSchemaOrError': {
        '__typename': 'RunConfigSchema',
        'rootDefaultYaml': '''execution:
  config:
    retries:
      enabled: {}
loggers: {}
ops:
  sum_op:
    inputs: {}
  sum_sq_op: {}
resources:
  io_manager: {}
'''
    }
}

snapshots['TestEnvironmentSchema.test_full_yaml[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        '__typename': 'RunConfigSchema',
        'rootDefaultYaml': '''execution:
  config:
    retries:
      enabled: {}
loggers: {}
ops:
  sum_op:
    inputs: {}
  sum_sq_op: {}
resources:
  io_manager: {}
'''
    }
}

snapshots['TestEnvironmentSchema.test_full_yaml[non_launchable_sqlite_instance_multi_location] 1'] = {
    'runConfigSchemaOrError': {
        '__typename': 'RunConfigSchema',
        'rootDefaultYaml': '''execution:
  config:
    retries:
      enabled: {}
loggers: {}
ops:
  sum_op:
    inputs: {}
  sum_sq_op: {}
resources:
  io_manager: {}
'''
    }
}
