# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_query_inputs_outputs 1'] = {
    'repositoryOrError': {
        'usedSolid': {
            '__typename': 'UsedSolid',
            'definition': {
                'inputDefinitions': [
                    {
                        'metadataEntries': [
                            {
                                'label': 'a'
                            }
                        ]
                    }
                ],
                'outputDefinitions': [
                    {
                        'metadataEntries': [
                            {
                                'label': 'c'
                            }
                        ]
                    }
                ]
            }
        }
    }
}
