# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestAssetAwareEventLog.test_get_asset_key_lineage[sqlite_with_default_run_launcher_managed_grpc_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                        {
                            'assetKey': {
                                'path': [
                                    'a'
                                ]
                            },
                            'partitions': [
                            ]
                        }
                    ],
                    'materialization': {
                        'label': 'b'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}

snapshots['TestAssetAwareEventLog.test_get_asset_key_materialization[asset_aware_instance_in_process_env] 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'assetLineage': [
                    ],
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ],
        'tags': [
        ]
    }
}
