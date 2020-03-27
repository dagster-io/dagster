# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_query_snapshot 1'] = {
    'pipelineSnapshot': {
        'description': None,
        'modes': [
            {
                'name': 'default'
            }
        ],
        'name': 'csv_hello_world',
        'runs': [
        ],
        'runtimeTypes': [
            {
                'key': 'Any'
            },
            {
                'key': 'Bool'
            },
            {
                'key': 'Float'
            },
            {
                'key': 'Int'
            },
            {
                'key': 'Nothing'
            },
            {
                'key': 'Path'
            },
            {
                'key': 'PoorMansDataFrame'
            },
            {
                'key': 'String'
            }
        ],
        'solidHandles': [
            {
                'handleID': 'sum_solid'
            },
            {
                'handleID': 'sum_sq_solid'
            }
        ],
        'solids': [
            {
                'name': 'sum_solid'
            },
            {
                'name': 'sum_sq_solid'
            }
        ],
        'tags': [
        ]
    }
}
