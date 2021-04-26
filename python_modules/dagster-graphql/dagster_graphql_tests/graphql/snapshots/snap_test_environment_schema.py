# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[readonly_in_memory_instance_lazy_repository] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { in_process?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } multiprocess?: { config?: { max_concurrent?: Int retries?: { disabled?: { } enabled?: { } } } } } intermediate_storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } loggers?: { console?: { config?: { log_level?: String name?: String } } } resources?: { io_manager?: { config?: Any } } solids: { sum_solid: { config?: Any inputs: { num: String } outputs?: [{ result?: String }] } sum_sq_solid?: { config?: Any outputs?: [{ result?: String }] } } storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } }".',
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
                    'message': 'Missing required config entry "solids" at the root. Minimal acceptable config for this path: {\'solids\': {\'sum_solid\': {\'inputs\': {\'num\': \'...\'}}}}',
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

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[readonly_in_memory_instance_managed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { in_process?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } multiprocess?: { config?: { max_concurrent?: Int retries?: { disabled?: { } enabled?: { } } } } } intermediate_storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } loggers?: { console?: { config?: { log_level?: String name?: String } } } resources?: { io_manager?: { config?: Any } } solids: { sum_solid: { config?: Any inputs: { num: String } outputs?: [{ result?: String }] } sum_sq_solid?: { config?: Any outputs?: [{ result?: String }] } } storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } }".',
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
                    'message': 'Missing required config entry "solids" at the root. Minimal acceptable config for this path: {\'solids\': {\'sum_solid\': {\'inputs\': {\'num\': \'...\'}}}}',
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

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[readonly_in_memory_instance_multi_location] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { in_process?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } multiprocess?: { config?: { max_concurrent?: Int retries?: { disabled?: { } enabled?: { } } } } } intermediate_storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } loggers?: { console?: { config?: { log_level?: String name?: String } } } resources?: { io_manager?: { config?: Any } } solids: { sum_solid: { config?: Any inputs: { num: String } outputs?: [{ result?: String }] } sum_sq_solid?: { config?: Any outputs?: [{ result?: String }] } } storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } }".',
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
                    'message': 'Missing required config entry "solids" at the root. Minimal acceptable config for this path: {\'solids\': {\'sum_solid\': {\'inputs\': {\'num\': \'...\'}}}}',
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

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[readonly_sqlite_instance_deployed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { in_process?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } multiprocess?: { config?: { max_concurrent?: Int retries?: { disabled?: { } enabled?: { } } } } } intermediate_storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } loggers?: { console?: { config?: { log_level?: String name?: String } } } resources?: { io_manager?: { config?: Any } } solids: { sum_solid: { config?: Any inputs: { num: String } outputs?: [{ result?: String }] } sum_sq_solid?: { config?: Any outputs?: [{ result?: String }] } } storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } }".',
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
                    'message': 'Missing required config entry "solids" at the root. Minimal acceptable config for this path: {\'solids\': {\'sum_solid\': {\'inputs\': {\'num\': \'...\'}}}}',
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

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[readonly_sqlite_instance_lazy_repository] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { in_process?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } multiprocess?: { config?: { max_concurrent?: Int retries?: { disabled?: { } enabled?: { } } } } } intermediate_storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } loggers?: { console?: { config?: { log_level?: String name?: String } } } resources?: { io_manager?: { config?: Any } } solids: { sum_solid: { config?: Any inputs: { num: String } outputs?: [{ result?: String }] } sum_sq_solid?: { config?: Any outputs?: [{ result?: String }] } } storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } }".',
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
                    'message': 'Missing required config entry "solids" at the root. Minimal acceptable config for this path: {\'solids\': {\'sum_solid\': {\'inputs\': {\'num\': \'...\'}}}}',
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

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[readonly_sqlite_instance_managed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { in_process?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } multiprocess?: { config?: { max_concurrent?: Int retries?: { disabled?: { } enabled?: { } } } } } intermediate_storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } loggers?: { console?: { config?: { log_level?: String name?: String } } } resources?: { io_manager?: { config?: Any } } solids: { sum_solid: { config?: Any inputs: { num: String } outputs?: [{ result?: String }] } sum_sq_solid?: { config?: Any outputs?: [{ result?: String }] } } storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } }".',
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
                    'message': 'Missing required config entry "solids" at the root. Minimal acceptable config for this path: {\'solids\': {\'sum_solid\': {\'inputs\': {\'num\': \'...\'}}}}',
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

snapshots['TestEnvironmentSchema.test_basic_invalid_config_on_run_config_schema[readonly_sqlite_instance_multi_location] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationInvalid',
            'errors': [
                {
                    '__typename': 'FieldNotDefinedConfigError',
                    'fieldName': 'nope',
                    'message': 'Received unexpected config entry "nope" at the root. Expected: "{ execution?: { in_process?: { config?: { marker_to_close?: String retries?: { disabled?: { } enabled?: { } } } } multiprocess?: { config?: { max_concurrent?: Int retries?: { disabled?: { } enabled?: { } } } } } intermediate_storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } loggers?: { console?: { config?: { log_level?: String name?: String } } } resources?: { io_manager?: { config?: Any } } solids: { sum_solid: { config?: Any inputs: { num: String } outputs?: [{ result?: String }] } sum_sq_solid?: { config?: Any outputs?: [{ result?: String }] } } storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { config?: Any } } }".',
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
                    'message': 'Missing required config entry "solids" at the root. Minimal acceptable config for this path: {\'solids\': {\'sum_solid\': {\'inputs\': {\'num\': \'...\'}}}}',
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

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_in_memory_instance_lazy_repository] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_in_memory_instance_managed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_in_memory_instance_multi_location] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_sqlite_instance_deployed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_sqlite_instance_lazy_repository] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_sqlite_instance_managed_grpc_env] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_sqlite_instance_multi_location] 1'] = {
    'runConfigSchemaOrError': {
        'isRunConfigValid': {
            '__typename': 'PipelineConfigValidationValid',
            'pipelineName': 'csv_hello_world'
        }
    }
}
