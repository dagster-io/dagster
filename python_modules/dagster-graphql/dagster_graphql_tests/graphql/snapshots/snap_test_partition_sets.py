# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_get_partition_sets_for_pipeline 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': [
                    'return_hello'
                ]
            }
        ]
    }
}

snapshots['test_get_partition_sets_for_pipeline 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PipelineNotFoundError',
        'message': 'Pipeline invalid_pipeline is not present in the currently loaded repository.'
    }
}
