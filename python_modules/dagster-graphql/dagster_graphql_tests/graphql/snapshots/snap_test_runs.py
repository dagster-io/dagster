# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_get_runs_over_graphql 1'] = {
    'environmentConfigYaml': '''resources:
  op:
    config: 2
''',
    'executionPlan': {
        'steps': [
            {
                'key': 'apply_to_three.compute'
            }
        ]
    },
    'mode': 'add_mode',
    'pipeline': {
        'name': 'multi_mode_with_resources'
    },
    'status': 'SUCCESS'
}

snapshots['test_get_runs_over_graphql 2'] = {
    'environmentConfigYaml': '''resources:
  op:
    config: 3
''',
    'executionPlan': {
        'steps': [
            {
                'key': 'apply_to_three.compute'
            }
        ]
    },
    'mode': 'add_mode',
    'pipeline': {
        'name': 'multi_mode_with_resources'
    },
    'status': 'SUCCESS'
}
