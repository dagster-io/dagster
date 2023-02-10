# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_fetch_top_level_resource 1'] = {
    'topLevelResourceDetailsOrError': {
        '__typename': 'ResourceDetails',
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
                'type': 'VALUE',
                'value': 'true'
            },
            {
                'key': 'a_string',
                'type': 'VALUE',
                'value': '"foo"'
            }
        ],
        'description': 'my description',
        'name': 'my_resource'
    }
}

snapshots['test_fetch_top_level_resources 1'] = {
    'allTopLevelResourceDetailsOrError': {
        '__typename': 'ResourceDetailsList',
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
                        'type': 'VALUE',
                        'value': 'true'
                    },
                    {
                        'key': 'a_string',
                        'type': 'VALUE',
                        'value': '"foo"'
                    }
                ],
                'description': 'my description',
                'name': 'my_resource'
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
                        'type': 'VALUE',
                        'value': 'false'
                    },
                    {
                        'key': 'a_string',
                        'type': 'ENV_VAR',
                        'value': 'MY_STRING'
                    }
                ],
                'description': 'my description',
                'name': 'my_resource_env_vars'
            }
        ]
    }
}
