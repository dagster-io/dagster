# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_fetch_top_level_resource 1'] = {
    'resourceDetailsOrError': {
        '__typename': 'ResourceDetails',
        'configFields': [
            {
                'configType': {
                    'key': 'StringSourceType'
                },
                'description': None,
                'name': 'a_string'
            },
            {
                'configType': {
                    'key': 'StringSourceType'
                },
                'description': None,
                'name': 'an_unset_string'
            }
        ],
        'configuredValues': [
            {
                'key': 'a_string',
                'type': 'VALUE',
                'value': '"foo"'
            },
            {
                'key': 'an_unset_string',
                'type': 'VALUE',
                'value': '"defaulted"'
            }
        ],
        'description': 'My description.',
        'name': 'my_resource'
    }
}
