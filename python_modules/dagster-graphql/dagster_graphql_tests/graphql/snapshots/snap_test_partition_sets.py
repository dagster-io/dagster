# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_postgres_instance_lazy_repository] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'alpha_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_postgres_instance_lazy_repository] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_postgres_instance_managed_grpc_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'alpha_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_postgres_instance_managed_grpc_env] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_postgres_instance_multi_location] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'alpha_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_postgres_instance_multi_location] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'alpha_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_deployed_grpc_env] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_lazy_repository] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'alpha_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_lazy_repository] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'alpha_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
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

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_multi_location] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'alpha_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            }
        ]
    }
}

snapshots['TestPartitionSets.test_get_partition_sets_for_pipeline[non_launchable_sqlite_instance_multi_location] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
        ]
    }
}
