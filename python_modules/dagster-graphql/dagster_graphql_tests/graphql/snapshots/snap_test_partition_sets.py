# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_in_memory_instance_lazy_repository] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''{}
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

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_in_memory_instance_lazy_repository] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_in_memory_instance_managed_grpc_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''{}
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

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_in_memory_instance_managed_grpc_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_in_memory_instance_multi_location] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''{}
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

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_in_memory_instance_multi_location] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_postgres_instance_multi_location] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''{}
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

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_postgres_instance_multi_location] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''{}
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

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_deployed_grpc_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_lazy_repository] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''{}
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

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_lazy_repository] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''{}
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

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_managed_grpc_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_multi_location] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitionsOrError': {
            'results': [
                {
                    'name': '0',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '1',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '2',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '3',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '4',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '5',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '6',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '7',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '8',
                    'runConfigOrError': {
                        'yaml': '''{}
'''
                    },
                    'tagsOrError': {
                        '__typename': 'PartitionTags'
                    }
                },
                {
                    'name': '9',
                    'runConfigOrError': {
                        'yaml': '''{}
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

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_multi_location] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}
