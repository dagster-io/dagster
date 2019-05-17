# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_mode_fetch_loggers 1'] = {
    'pipeline': {
        'modes': [
            {
                'loggers': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'log_level'
                                    },
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'prefix'
                                    }
                                ],
                                'name': None
                            }
                        },
                        'description': None,
                        'name': 'bar'
                    }
                ],
                'name': 'bar_mode'
            },
            {
                'loggers': [
                    {
                        'configField': {
                            'configType': {
                                'name': 'String'
                            }
                        },
                        'description': None,
                        'name': 'foo'
                    }
                ],
                'name': 'foo_mode'
            },
            {
                'loggers': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'log_level'
                                    },
                                    {
                                        'configType': {
                                            'name': 'String'
                                        },
                                        'name': 'prefix'
                                    }
                                ],
                                'name': None
                            }
                        },
                        'description': None,
                        'name': 'bar'
                    },
                    {
                        'configField': {
                            'configType': {
                                'name': 'String'
                            }
                        },
                        'description': None,
                        'name': 'foo'
                    }
                ],
                'name': 'foobar_mode'
            }
        ]
    }
}
