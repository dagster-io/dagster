# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

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
                    'message': 'Undefined field "nope" at document config root. Expected: "{ execution?: { in_process?: { config?: { marker_to_close?: String retries?: { deferred?: { previous_attempts?: { } } disabled?: { } enabled?: { } } } } multiprocess?: { config?: { max_concurrent?: Int retries?: { deferred?: { previous_attempts?: { } } disabled?: { } enabled?: { } } } } } loggers?: { console?: { config?: { log_level?: String name?: String } } } resources?: { } solids: { sum_solid: { inputs: { num: Path } outputs?: [{ result?: Path }] } sum_sq_solid?: { outputs?: [{ result?: Path }] } } storage?: { filesystem?: { config?: { base_dir?: String } } in_memory?: { } } }"',
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
                    'message': 'Missing required field "solids" at document config root. Available Fields: "[\'execution\', \'loggers\', \'resources\', \'solids\', \'storage\']".',
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
