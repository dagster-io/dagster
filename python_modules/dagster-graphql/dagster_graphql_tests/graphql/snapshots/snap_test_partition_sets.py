# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestPartitionSets.test_get_partition_set[readonly_in_memory_instance_in_process_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
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
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_in_memory_instance_in_process_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_in_memory_instance_out_of_process_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
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
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_in_memory_instance_out_of_process_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_sqlite_instance_in_process_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
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
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_sqlite_instance_in_process_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_sqlite_instance_out_of_process_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
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
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_sqlite_instance_out_of_process_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[readonly_sqlite_instance_multi_location] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'run_config_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[readonly_sqlite_instance_multi_location] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_in_memory_instance_multi_location] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
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
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_in_memory_instance_multi_location] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_sqlite_instance_multi_location] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
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
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_set[readonly_sqlite_instance_multi_location] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}
