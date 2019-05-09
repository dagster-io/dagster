# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_query_multi_mode 1'] = [
    {
        'description': 'Mode that adds things',
        'name': 'add_mode',
        'resources': [
            {
                'name': 'op'
            }
        ]
    },
    {
        'description': 'Mode that multiplies things',
        'name': 'mult_mode',
        'resources': [
            {
                'name': 'op'
            }
        ]
    },
    {
        'description': 'Mode that adds two numbers to thing',
        'name': 'double_adder',
        'resources': [
            {
                'name': 'op'
            }
        ]
    }
]
