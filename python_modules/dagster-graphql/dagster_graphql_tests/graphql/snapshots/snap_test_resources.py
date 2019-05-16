# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_mode_fetch_resources 1'] = {
    'pipeline': {
        'modes': [
            {
                'name': 'add_mode',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'name': 'Int'
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
                                            'name': 'Int'
                                        },
                                        'name': 'num_one'
                                    },
                                    {
                                        'configType': {
                                            'name': 'Int'
                                        },
                                        'name': 'num_two'
                                    }
                                ],
                                'name': None
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
                                'name': 'Int'
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
