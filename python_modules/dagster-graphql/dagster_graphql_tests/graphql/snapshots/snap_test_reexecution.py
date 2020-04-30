# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_full_pipeline_reexecution_fs_storage 1'] = {
    'startPipelineExecution': {
        '__typename': 'StartPipelineRunSuccess',
        'run': {
            'pipeline': {
                'name': 'csv_hello_world'
            },
            'tags': [
            ]
        }
    }
}

snapshots['test_full_pipeline_reexecution_in_memory_storage 1'] = {
    'startPipelineExecution': {
        '__typename': 'StartPipelineRunSuccess',
        'run': {
            'pipeline': {
                'name': 'csv_hello_world'
            },
            'tags': [
            ]
        }
    }
}
