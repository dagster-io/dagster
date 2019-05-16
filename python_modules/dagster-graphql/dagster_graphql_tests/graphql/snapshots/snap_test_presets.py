# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_basic_preset_query_with_presets 1'] = {
    'presetsForPipeline': [
        {
            '__typename': 'PipelinePreset',
            'environment': '''solids:
  sum_solid:
    inputs:
      num: data/num_prod.csv
''',
            'name': 'prod',
            'solidSubset': None
        },
        {
            '__typename': 'PipelinePreset',
            'environment': '''solids:
  sum_solid:
    inputs:
      num: data/num.csv
''',
            'name': 'test',
            'solidSubset': None
        }
    ]
}
