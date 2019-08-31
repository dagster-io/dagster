# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_basic_preset_query_with_presets 1'] = {
    'pipeline': {
        'name': 'csv_hello_world',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  sum_solid:
    inputs:
      num: data/num_prod.csv
''',
                'mode': 'default',
                'name': 'prod',
                'solidSubset': None
            },
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  sum_solid:
    inputs:
      num: data/num.csv
''',
                'mode': 'default',
                'name': 'test',
                'solidSubset': None
            },
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  sum_solid:
    inputs:
      num: /data/num.csv
''',
                'mode': 'default',
                'name': 'test_inline',
                'solidSubset': None
            }
        ]
    }
}
