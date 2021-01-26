# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestPresets.test_basic_preset_query_with_presets[readonly_in_memory_instance_in_process_env] 1'] = {
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
                'solidSelection': None
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
                'solidSelection': None
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
                'solidSelection': None
            }
        ]
    }
}
