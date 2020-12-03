# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestComputeLogs.test_get_compute_logs_over_graphql[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'stdout': {
        'data': '''HELLO WORLD
'''
    }
}
