# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_get_all_asset_keys 1'] = {
    'assetsOrError': {
        '__typename': 'AssetConnection',
        'nodes': [
            {
                'key': 'c'
            },
            {
                'key': 'b'
            },
            {
                'key': 'a'
            }
        ]
    }
}

snapshots['test_get_asset_key_materialization 1'] = {
    'assetOrError': {
        'assetMaterializations': [
            {
                'materializationEvent': {
                    'materialization': {
                        'label': 'a'
                    }
                }
            }
        ]
    }
}
