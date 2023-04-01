# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integers_partition_set',
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
        'pipelineName': 'integers',
        'solidSelection': None
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_managed_grpc_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestPartitionSets.test_get_partition_set[non_launchable_sqlite_instance_managed_grpc_env] 3'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'dynamic_partitioned_assets_job_partition_set',
        'partitionsOrError': {
            'results': [
            ]
        },
        'pipelineName': 'dynamic_partitioned_assets_job',
        'solidSelection': None
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'integers_partition_set',
                'pipelineName': 'integers',
                'solidSelection': None
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_managed_grpc_env] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}
