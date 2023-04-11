# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_mode_fetch_resources 1'] = {
    'pipelineOrError': {
        '__typename': 'Pipeline',
        'modes': [
            {
                'name': 'default',
                'resources': [
                    {
                        'configField': {
                            'configType': {
                                'key': 'Int'
                            }
                        },
                        'description': None,
                        'name': 'R1'
                    },
                    {
                        'configField': {
                            'configType': {
                                'key': 'Any'
                            }
                        },
                        'description': 'Built-in filesystem IO manager that stores and retrieves values using pickling.',
                        'name': 'io_manager'
                    }
                ]
            }
        ]
    }
}

snapshots['test_required_resources 1'] = {
    'pipelineOrError': {
        'name': 'required_resource_job',
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
