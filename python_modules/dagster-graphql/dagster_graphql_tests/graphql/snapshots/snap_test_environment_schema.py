# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_in_memory_instance_in_process_env] 1'] = {
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

snapshots['TestEnvironmentSchema.test_basic_valid_config_on_run_config_schema[readonly_sqlite_instance_in_process_env] 1'] = {
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
