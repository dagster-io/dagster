# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_mode_fetch_loggers 1'] = {
    'pipelineOrError': {
        '__typename': 'Pipeline',
        'modes': [
            {
                'loggers': [
                    {
                        'configField': {
                            'configType': {
                                'fields': [
                                    {
                                        'configType': {
                                            'key': 'String'
                                        },
                                        'name': 'log_level'
                                    },
                                    {
                                        'configType': {
                                            'key': 'String'
                                        },
                                        'name': 'prefix'
                                    }
                                ],
                                'key': 'Shape.37a85e53844c27abff7868c5c2e6a32d7fd1c308'
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
                                'key': 'String'
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
                                            'key': 'String'
                                        },
                                        'name': 'log_level'
                                    },
                                    {
                                        'configType': {
                                            'key': 'String'
                                        },
                                        'name': 'prefix'
                                    }
                                ],
                                'key': 'Shape.37a85e53844c27abff7868c5c2e6a32d7fd1c308'
                            }
                        },
                        'description': None,
                        'name': 'bar'
                    },
                    {
                        'configField': {
                            'configType': {
                                'key': 'String'
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
