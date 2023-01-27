# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_fetch_top_level_resource 1'] = {
    'topLevelResourceOrError': {
        '__typename': 'TopLevelResource',
        'configFields': [
            {
                'configType': {
                    'key': 'BoolSourceType'
                },
                'description': None,
                'name': 'a_bool'
            },
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
                'key': 'a_bool',
                'value': 'true'
            },
            {
                'key': 'a_string',
                'value': '"foo"'
            }
        ],
        'description': 'my description',
        'name': 'my_resource'
    }
}

snapshots['test_fetch_top_level_resources 1'] = {
    'topLevelResourcesOrError': {
        '__typename': 'TopLevelResources',
        'results': [
            {
                'configFields': [
                ],
                'configuredValues': [
                ],
                'description': None,
                'name': 'foo'
            },
            {
                'configFields': [
                    {
                        'configType': {
                            'key': 'BoolSourceType'
                        },
                        'description': None,
                        'name': 'a_bool'
                    },
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
                        'key': 'a_bool',
                        'value': 'true'
                    },
                    {
                        'key': 'a_string',
                        'value': '"foo"'
                    }
                ],
                'description': 'my description',
                'name': 'my_resource'
            }
        ]
    }
}
