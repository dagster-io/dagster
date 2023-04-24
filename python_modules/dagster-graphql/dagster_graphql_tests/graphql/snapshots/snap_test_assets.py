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
                        'diamond_source'
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
                        'downstream_dynamic_partitioned_asset'
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
                        'downstream_weekly_partitioned_asset'
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
                        'dynamic_in_multipartitions_fail'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dynamic_in_multipartitions_success'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fail_partition_materialization'
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
                        'fresh_diamond_bottom'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_left'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_right'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_top'
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
                        'hanging_partition_asset'
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
                        'middle_static_partitioned_asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'middle_static_partitioned_asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_fail'
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
                        'no_multipartitions_1'
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
                        'unpartitioned_upstream_of_partitioned'
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
                        'upstream_daily_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_dynamic_partitioned_asset'
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
                        'diamond_source'
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
                        'downstream_dynamic_partitioned_asset'
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
                        'downstream_weekly_partitioned_asset'
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
                        'dynamic_in_multipartitions_fail'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dynamic_in_multipartitions_success'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fail_partition_materialization'
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
                        'fresh_diamond_bottom'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_left'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_right'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_top'
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
                        'hanging_partition_asset'
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
                        'middle_static_partitioned_asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'middle_static_partitioned_asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_fail'
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
                        'no_multipartitions_1'
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
                        'unpartitioned_upstream_of_partitioned'
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
                        'upstream_daily_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_dynamic_partitioned_asset'
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
                        'diamond_source'
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
                        'downstream_dynamic_partitioned_asset'
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
                        'downstream_weekly_partitioned_asset'
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
                        'dynamic_in_multipartitions_fail'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dynamic_in_multipartitions_success'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fail_partition_materialization'
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
                        'fresh_diamond_bottom'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_left'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_right'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_top'
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
                        'hanging_partition_asset'
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
                        'middle_static_partitioned_asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'middle_static_partitioned_asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_fail'
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
                        'no_multipartitions_1'
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
                        'unpartitioned_upstream_of_partitioned'
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
                        'upstream_daily_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_dynamic_partitioned_asset'
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
                        'diamond_source'
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
                        'downstream_dynamic_partitioned_asset'
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
                        'downstream_weekly_partitioned_asset'
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
                        'dynamic_in_multipartitions_fail'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'dynamic_in_multipartitions_success'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fail_partition_materialization'
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
                        'fresh_diamond_bottom'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_left'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_right'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'fresh_diamond_top'
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
                        'hanging_partition_asset'
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
                        'middle_static_partitioned_asset_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'middle_static_partitioned_asset_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_1'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_2'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'multipartitions_fail'
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
                        'no_multipartitions_1'
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
                        'unpartitioned_upstream_of_partitioned'
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
                        'upstream_daily_partitioned_asset'
                    ]
                }
            },
            {
                'key': {
                    'path': [
                        'upstream_dynamic_partitioned_asset'
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

snapshots['TestAssetAwareEventLog.test_asset_op[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetOrError': {
        'definition': {
            'op': {
                'description': None,
                'inputDefinitions': [
                    {
                        'name': 'asset_one'
                    }
                ],
                'name': 'asset_two',
                'outputDefinitions': [
                    {
                        'name': 'result'
                    }
                ]
            }
        }
    }
}

snapshots['TestAssetAwareEventLog.test_asset_op[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'definition': {
            'op': {
                'description': None,
                'inputDefinitions': [
                    {
                        'name': 'asset_one'
                    }
                ],
                'name': 'asset_two',
                'outputDefinitions': [
                    {
                        'name': 'result'
                    }
                ]
            }
        }
    }
}

snapshots['TestAssetAwareEventLog.test_asset_op[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetOrError': {
        'definition': {
            'op': {
                'description': None,
                'inputDefinitions': [
                    {
                        'name': 'asset_one'
                    }
                ],
                'name': 'asset_two',
                'outputDefinitions': [
                    {
                        'name': 'result'
                    }
                ]
            }
        }
    }
}

snapshots['TestAssetAwareEventLog.test_asset_op[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'definition': {
            'op': {
                'description': None,
                'inputDefinitions': [
                    {
                        'name': 'asset_one'
                    }
                ],
                'name': 'asset_two',
                'outputDefinitions': [
                    {
                        'name': 'result'
                    }
                ]
            }
        }
    }
}

snapshots['TestAssetAwareEventLog.test_freshness_info[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetNodes': [
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dummy_source_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["diamond_source"]'
        },
        {
            'freshnessInfo': {
                'currentMinutesLate': 0.0,
                'latestMaterializationMinutesLate': None
            },
            'freshnessPolicy': {
                'cronSchedule': None,
                'maximumLagMinutes': 30.0
            },
            'id': 'test.test_repo.["fresh_diamond_bottom"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_left"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_right"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_top"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["int_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["str_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["no_multipartitions_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["typed_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["unpartitioned_upstream_of_partitioned"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["untyped_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_fail"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dynamic_in_multipartitions_fail"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dynamic_in_multipartitions_success"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_daily_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_weekly_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_dynamic_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_dynamic_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fail_partition_materialization"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_3"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["bar"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["baz"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["foo"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["foo_bar"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["unconnected"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_graph"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["first_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["never_runs_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_partition_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_4"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["ungrouped_asset_3"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["ungrouped_asset_5"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_yields_observation"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["yield_partition_materialization"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_static_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["middle_static_partitioned_asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["middle_static_partitioned_asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_static_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_time_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_time_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_one"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_two"]'
        }
    ]
}

snapshots['TestAssetAwareEventLog.test_freshness_info[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetNodes': [
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dummy_source_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["diamond_source"]'
        },
        {
            'freshnessInfo': {
                'currentMinutesLate': 0.0,
                'latestMaterializationMinutesLate': None
            },
            'freshnessPolicy': {
                'cronSchedule': None,
                'maximumLagMinutes': 30.0
            },
            'id': 'test.test_repo.["fresh_diamond_bottom"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_left"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_right"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_top"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["int_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["str_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["no_multipartitions_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["typed_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["unpartitioned_upstream_of_partitioned"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["untyped_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_fail"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dynamic_in_multipartitions_fail"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dynamic_in_multipartitions_success"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_daily_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_weekly_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_dynamic_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_dynamic_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fail_partition_materialization"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_3"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["bar"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["baz"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["foo"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["foo_bar"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["unconnected"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_graph"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["first_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["never_runs_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_partition_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_4"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["ungrouped_asset_3"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["ungrouped_asset_5"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_yields_observation"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["yield_partition_materialization"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_static_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["middle_static_partitioned_asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["middle_static_partitioned_asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_static_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_time_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_time_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_one"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_two"]'
        }
    ]
}

snapshots['TestAssetAwareEventLog.test_freshness_info[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetNodes': [
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dummy_source_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["diamond_source"]'
        },
        {
            'freshnessInfo': {
                'currentMinutesLate': 0.0,
                'latestMaterializationMinutesLate': None
            },
            'freshnessPolicy': {
                'cronSchedule': None,
                'maximumLagMinutes': 30.0
            },
            'id': 'test.test_repo.["fresh_diamond_bottom"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_left"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_right"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_top"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["int_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["str_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["no_multipartitions_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["typed_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["unpartitioned_upstream_of_partitioned"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["untyped_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_fail"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dynamic_in_multipartitions_fail"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dynamic_in_multipartitions_success"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_daily_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_weekly_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_dynamic_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_dynamic_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fail_partition_materialization"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_3"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["bar"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["baz"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["foo"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["foo_bar"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["unconnected"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_graph"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["first_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["never_runs_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_partition_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_4"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["ungrouped_asset_3"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["ungrouped_asset_5"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_yields_observation"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["yield_partition_materialization"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_static_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["middle_static_partitioned_asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["middle_static_partitioned_asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_static_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_time_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_time_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_one"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_two"]'
        }
    ]
}

snapshots['TestAssetAwareEventLog.test_freshness_info[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetNodes': [
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dummy_source_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["diamond_source"]'
        },
        {
            'freshnessInfo': {
                'currentMinutesLate': 0.0,
                'latestMaterializationMinutesLate': None
            },
            'freshnessPolicy': {
                'cronSchedule': None,
                'maximumLagMinutes': 30.0
            },
            'id': 'test.test_repo.["fresh_diamond_bottom"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_left"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_right"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fresh_diamond_top"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["int_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["str_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["no_multipartitions_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["typed_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["unpartitioned_upstream_of_partitioned"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["untyped_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["multipartitions_fail"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dynamic_in_multipartitions_fail"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["dynamic_in_multipartitions_success"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_daily_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_weekly_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_dynamic_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_dynamic_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["fail_partition_materialization"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_3"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["bar"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["baz"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["foo"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["foo_bar"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["unconnected"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_graph"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["first_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["never_runs_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["hanging_partition_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["grouped_asset_4"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["ungrouped_asset_3"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["ungrouped_asset_5"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_yields_observation"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["yield_partition_materialization"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_static_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["middle_static_partitioned_asset_1"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["middle_static_partitioned_asset_2"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_static_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["downstream_time_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["upstream_time_partitioned_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_one"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["asset_two"]'
        }
    ]
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'assetLineage': [
                ],
                'label': 'a'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'assetLineage': [
                ],
                'label': 'a'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'assetLineage': [
                ],
                'label': 'a'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'assetLineage': [
                ],
                'label': 'a'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_not_found[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        '__typename': 'AssetNotFoundError'
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'label': 'a',
                'partition': 'partition_1'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'label': 'a',
                'partition': 'partition_1'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'label': 'a',
                'partition': 'partition_1'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_partitioned_asset_key_materialization[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'label': 'a',
                'partition': 'partition_1'
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_run_materialization[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'runsOrError': {
        'results': [
            {
                'assetMaterializations': [
                    {
                        'assetKey': {
                            'path': [
                                'a'
                            ]
                        }
                    }
                ]
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_run_materialization[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'runsOrError': {
        'results': [
            {
                'assetMaterializations': [
                    {
                        'assetKey': {
                            'path': [
                                'a'
                            ]
                        }
                    }
                ]
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_run_materialization[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'runsOrError': {
        'results': [
            {
                'assetMaterializations': [
                    {
                        'assetKey': {
                            'path': [
                                'a'
                            ]
                        }
                    }
                ]
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_run_materialization[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'runsOrError': {
        'results': [
            {
                'assetMaterializations': [
                    {
                        'assetKey': {
                            'path': [
                                'a'
                            ]
                        }
                    }
                ]
            }
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_op_assets[postgres_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'repositoryOrError': {
        'usedSolid': {
            'definition': {
                'assetNodes': [
                    {
                        'assetKey': {
                            'path': [
                                'asset_two'
                            ]
                        }
                    }
                ]
            }
        }
    }
}

snapshots['TestAssetAwareEventLog.test_op_assets[postgres_with_default_run_launcher_managed_grpc_env] 1'] = {
    'repositoryOrError': {
        'usedSolid': {
            'definition': {
                'assetNodes': [
                    {
                        'assetKey': {
                            'path': [
                                'asset_two'
                            ]
                        }
                    }
                ]
            }
        }
    }
}

snapshots['TestAssetAwareEventLog.test_op_assets[sqlite_with_default_run_launcher_deployed_grpc_env] 1'] = {
    'repositoryOrError': {
        'usedSolid': {
            'definition': {
                'assetNodes': [
                    {
                        'assetKey': {
                            'path': [
                                'asset_two'
                            ]
                        }
                    }
                ]
            }
        }
    }
}

snapshots['TestAssetAwareEventLog.test_op_assets[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'repositoryOrError': {
        'usedSolid': {
            'definition': {
                'assetNodes': [
                    {
                        'assetKey': {
                            'path': [
                                'asset_two'
                            ]
                        }
                    }
                ]
            }
        }
    }
}
