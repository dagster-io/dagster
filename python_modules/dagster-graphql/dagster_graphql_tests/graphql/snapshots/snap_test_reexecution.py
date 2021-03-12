# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestReexecution.test_full_pipeline_reexecution_fs_storage[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'launchPipelineExecution': {
        '__typename': 'LaunchPipelineRunSuccess',
        'run': {
            'mode': 'default',
            'pipeline': {
                'name': 'csv_hello_world'
            },
            'runConfigYaml': '<runConfigYaml dummy value>',
            'runId': '<runId dummy value>',
            'status': 'STARTING',
            'tags': [
            ]
        }
    }
}

snapshots['TestReexecution.test_full_pipeline_reexecution_fs_storage[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'launchPipelineExecution': {
        '__typename': 'LaunchPipelineRunSuccess',
        'run': {
            'mode': 'default',
            'pipeline': {
                'name': 'csv_hello_world'
            },
            'runConfigYaml': '<runConfigYaml dummy value>',
            'runId': '<runId dummy value>',
            'status': 'STARTING',
            'tags': [
            ]
        }
    }
}

snapshots['TestReexecution.test_full_pipeline_reexecution_in_memory_storage[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'launchPipelineExecution': {
        '__typename': 'LaunchPipelineRunSuccess',
        'run': {
            'mode': 'default',
            'pipeline': {
                'name': 'csv_hello_world'
            },
            'runConfigYaml': '<runConfigYaml dummy value>',
            'runId': '<runId dummy value>',
            'status': 'STARTING',
            'tags': [
            ]
        }
    }
}

snapshots['TestReexecution.test_full_pipeline_reexecution_in_memory_storage[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'launchPipelineExecution': {
        '__typename': 'LaunchPipelineRunSuccess',
        'run': {
            'mode': 'default',
            'pipeline': {
                'name': 'csv_hello_world'
            },
            'runConfigYaml': '<runConfigYaml dummy value>',
            'runId': '<runId dummy value>',
            'status': 'STARTING',
            'tags': [
            ]
        }
    }
}
