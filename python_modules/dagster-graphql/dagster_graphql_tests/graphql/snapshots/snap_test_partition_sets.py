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
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''intermediate_storage:
  filesystem: {}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
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

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[readonly_in_memory_instance_in_process_env] 1'] = {
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
            },
            {
                'mode': 'default',
                'name': 'timezone_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[readonly_in_memory_instance_in_process_env] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}
