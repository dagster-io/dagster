# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestComputeLogs.test_compute_logs_subscription_graphql[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = [
    {
        'computeLogs': {
            'data': '''HELLO WORLD
'''
        }
    }
]
