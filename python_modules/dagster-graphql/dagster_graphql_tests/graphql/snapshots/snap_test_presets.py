# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_basic_preset_query_with_presets 1'] = {
    'pipelineOrError': {
        'name': 'csv_hello_world',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'default',
                'name': 'prod',
                'runConfigYaml': '''solids:
  sum_solid:
    inputs:
      num: data/num_prod.csv
''',
                'solidSubset': None
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'default',
                'name': 'test',
                'runConfigYaml': '''solids:
  sum_solid:
    inputs:
      num: data/num.csv
''',
                'solidSubset': None
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'default',
                'name': 'test_inline',
                'runConfigYaml': '''solids:
  sum_solid:
    inputs:
      num: /data/num.csv
''',
                'solidSubset': None
            }
        ]
    }
}
