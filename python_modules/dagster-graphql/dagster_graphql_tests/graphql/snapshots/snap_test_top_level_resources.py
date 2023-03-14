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
        'description': 'my description',
        'name': 'my_resource'
    }
}

snapshots['test_fetch_top_level_resource_env_var 1'] = {
    'topLevelResourceDetailsOrError': {
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
                'type': 'ENV_VAR',
                'value': 'MY_STRING'
            },
            {
                'key': 'an_unset_string',
                'type': 'VALUE',
                'value': '"defaulted"'
            }
        ],
        'description': 'my description',
        'name': 'my_resource_env_vars'
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
                'description': 'my description',
                'name': 'my_resource'
            },
            {
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
                        'type': 'ENV_VAR',
                        'value': 'MY_STRING'
                    },
                    {
                        'key': 'an_unset_string',
                        'type': 'VALUE',
                        'value': '"defaulted"'
                    }
                ],
                'description': 'my description',
                'name': 'my_resource_env_vars'
            },
            {
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
                        'type': 'ENV_VAR',
                        'value': 'MY_STRING'
                    },
                    {
                        'key': 'an_unset_string',
                        'type': 'ENV_VAR',
                        'value': 'MY_OTHER_STRING'
                    }
                ],
                'description': 'my description',
                'name': 'my_resource_two_env_vars'
            }
        ]
    }
}
