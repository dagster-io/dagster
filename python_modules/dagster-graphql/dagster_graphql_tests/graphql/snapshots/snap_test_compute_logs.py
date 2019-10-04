# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_get_compute_logs_over_graphql 1'] = {
    'stdout': {
        'data': '''HELLO WORLD
'''
    }
}

snapshots['test_compute_logs_subscription_graphql 1'] = [
    {
        'computeLogs': {
            'data': '''HELLO WORLD
'''
        }
    }
]
