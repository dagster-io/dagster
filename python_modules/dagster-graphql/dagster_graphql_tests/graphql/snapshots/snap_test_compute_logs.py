# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots[
    'TestComputeLogs.test_get_compute_logs_over_graphql[in_memory_instance_in_process_env] 1'
] = {
    'stdout': {
        'data': '''HELLO WORLD
'''
    }
}

snapshots[
    'TestComputeLogs.test_compute_logs_subscription_graphql[sqlite_with_sync_run_launcher_in_process_env] 1'
] = [
    {
        'computeLogs': {
            'data': '''HELLO WORLD
'''
        }
    }
]

snapshots[
    'TestComputeLogs.test_compute_logs_subscription_graphql[in_memory_instance_in_process_env] 1'
] = [
    {
        'computeLogs': {
            'data': '''HELLO WORLD
'''
        }
    }
]

snapshots[
    'TestComputeLogs.test_get_compute_logs_over_graphql[sqlite_with_sync_run_launcher_in_process_env] 1'
] = {
    'stdout': {
        'data': '''HELLO WORLD
'''
    }
}

snapshots[
    'TestComputeLogs.test_get_compute_logs_over_graphql[sqlite_with_default_run_launcher_in_process_env] 1'
] = {
    'stdout': {
        'data': '''HELLO WORLD
'''
    }
}

snapshots[
    'TestComputeLogs.test_compute_logs_subscription_graphql[sqlite_with_default_run_launcher_in_process_env] 1'
] = [
    {
        'computeLogs': {
            'data': '''HELLO WORLD
'''
        }
    }
]
