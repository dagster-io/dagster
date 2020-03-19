# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_get_all_partition_sets 1'] = {
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
            },
            {
                'mode': 'default',
                'name': 'enum_partition',
                'pipelineName': 'noop_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'no_config_pipeline_daily',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'no_config_pipeline_daily',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'foo_mode',
                'name': 'multi_mode_with_loggers_daily',
                'pipelineName': 'multi_mode_with_loggers',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'no_config_chain_pipeline_hourly',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSubset': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'no_config_chain_pipeline_daily',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSubset': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'no_config_chain_pipeline_monthly',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSubset': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'no_config_chain_pipeline_weekly',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSubset': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'no_config_pipeline_daily',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'no_config_pipeline_daily',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            }
        ]
    }
}

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
            },
            {
                'mode': 'default',
                'name': 'no_config_pipeline_daily',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'no_config_pipeline_daily',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'no_config_pipeline_daily',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
            },
            {
                'mode': 'default',
                'name': 'no_config_pipeline_daily',
                'pipelineName': 'no_config_pipeline',
                'solidSubset': None
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

snapshots['test_get_partition_set 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': [
            {
                'name': '0'
            },
            {
                'name': '1'
            },
            {
                'name': '2'
            },
            {
                'name': '3'
            },
            {
                'name': '4'
            },
            {
                'name': '5'
            },
            {
                'name': '6'
            },
            {
                'name': '7'
            },
            {
                'name': '8'
            },
            {
                'name': '9'
            }
        ],
        'pipelineName': 'no_config_pipeline',
        'solidSubset': [
            'return_hello'
        ]
    }
}

snapshots['test_get_partition_set 2'] = {
    'partitionSetOrError': {
        '__typename': 'PythonError'
    }
}
