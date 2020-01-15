# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_mode_fetch_resources 1'] = {
    'pipeline': {
        '__typename': 'Pipeline',
        'modes': [
            {
                'name': 'add_mode',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'key': 'Int'
                            }
                        },
                        'description': None,
                        'name': 'op'
                    }
                ]
            },
            {
                'name': 'double_adder',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'key': 'Int'
                                        },
                                        'name': 'num_one'
                                    },
                                    {
                                        'configType': {
                                            'key': 'Int'
                                        },
                                        'name': 'num_two'
                                    }
                                ],
                                'key': 'Shape.46ed531fb407db3450eaf305b9b22d72e404a01f'
                            }
                        },
                        'description': None,
                        'name': 'op'
                    }
                ]
            },
            {
                'name': 'mult_mode',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'key': 'Int'
                            }
                        },
                        'description': None,
                        'name': 'op'
                    }
                ]
            }
        ]
    }
}

snapshots['test_required_resources 1'] = {
    'pipeline': {
        'name': 'required_resource_pipeline',
        'solids': [
            {
                'definition': {
                    'requiredResources': [
                        {
                            'resourceKey': 'R1'
                        }
                    ]
                }
            }
        ]
    }
}
