# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAssetAwareEventLog.test_all_asset_keys[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_3'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_one'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_two'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_yields_observation'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'bar'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'baz'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_static_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_time_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dummy_source_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'first_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'foo'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'foo_bar'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_4'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_graph'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'int_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'never_runs_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'str_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'typed_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'unconnected'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'ungrouped_asset_3'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'ungrouped_asset_5'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'untyped_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_static_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_time_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'yield_partition_materialization'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_all_asset_keys[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_3'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_one'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_two'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_yields_observation'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'bar'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'baz'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_static_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_time_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dummy_source_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'first_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'foo'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'foo_bar'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_4'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_graph'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'int_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'never_runs_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'str_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'typed_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'unconnected'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'ungrouped_asset_3'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'ungrouped_asset_5'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'untyped_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_static_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_time_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'yield_partition_materialization'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_all_asset_keys[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_3'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_one'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_two'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_yields_observation'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'bar'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'baz'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_static_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_time_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dummy_source_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'first_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'foo'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'foo_bar'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_4'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_graph'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'int_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'never_runs_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'str_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'typed_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'unconnected'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'ungrouped_asset_3'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'ungrouped_asset_5'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'untyped_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_static_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_time_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'yield_partition_materialization'
                    ]
                }
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_all_asset_keys[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': {
                    'path': [
                        'a'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_3'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_one'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_two'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'asset_yields_observation'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'b'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'bar'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'baz'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'c'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_static_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'downstream_time_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dummy_source_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'first_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'foo'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'foo_bar'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'grouped_asset_4'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'hanging_graph'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'int_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'never_runs_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'str_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'typed_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'unconnected'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'ungrouped_asset_3'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'ungrouped_asset_5'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'untyped_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_static_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_time_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'yield_partition_materialization'
                    ]
                }
            }
        ]
    }
}
