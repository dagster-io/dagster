# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

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
                'latestMaterializationMinutesLate': 0.0
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
            'id': 'test.test_repo.["typed_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["untyped_asset"]'
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
                'latestMaterializationMinutesLate': 0.0
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
            'id': 'test.test_repo.["typed_asset"]'
        },
        {
            'freshnessInfo': None,
            'freshnessPolicy': None,
            'id': 'test.test_repo.["untyped_asset"]'
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
