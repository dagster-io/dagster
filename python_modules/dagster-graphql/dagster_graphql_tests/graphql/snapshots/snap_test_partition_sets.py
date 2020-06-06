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
                'mode': 'foo_mode',
                'name': 'partition_based_multi_mode_decorator_partitions',
                'pipelineName': 'multi_mode_with_loggers',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'solid_selection_daily_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': ['return_foo'],
            },
            {
                'mode': 'default',
                'name': 'solid_selection_hourly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': ['return_foo'],
            },
            {
                'mode': 'default',
                'name': 'solid_selection_monthly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': ['return_foo'],
            },
            {
                'mode': 'default',
                'name': 'solid_selection_weekly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': ['return_foo'],
            },
            {
                'mode': 'default',
                'name': 'environment_dict_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': ['return_hello'],
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'enum_partition',
                'pipelineName': 'noop_pipeline',
                'solidSelection': None,
            },
        ],
    }
}

snapshots['test_get_partition_sets_for_pipeline 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'environment_dict_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': ['return_hello'],
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None,
            },
        ],
    }
}

snapshots['test_get_partition_sets_for_pipeline 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PipelineNotFoundError',
        'message': 'Could not find Pipeline <<in_process>>.test_repo.invalid_pipeline',
    }
}

snapshots['test_get_partition_set 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
                {'name': '0'},
                {'name': '1'},
                {'name': '2'},
                {'name': '3'},
                {'name': '4'},
                {'name': '5'},
                {'name': '6'},
                {'name': '7'},
                {'name': '8'},
                {'name': '9'},
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': ['return_hello'],
    }
}

snapshots['test_get_partition_set 2'] = {
    'partitionSetOrError': {'__typename': 'PartitionSetNotFoundError'}
}
