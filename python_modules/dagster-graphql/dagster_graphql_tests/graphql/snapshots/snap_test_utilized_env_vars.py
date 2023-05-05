# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_get_used_env_vars 1'] = {
    'utilizedEnvVarsOrError': {
        '__typename': 'EnvVarWithConsumersList',
        'results': [
            {
                'envVarConsumers': [
                    {
                        'name': 'my_resource_two_env_vars',
                        'type': 'RESOURCE'
                    }
                ],
                'envVarName': 'MY_OTHER_STRING'
            },
            {
                'envVarConsumers': [
                    {
                        'name': 'my_resource_env_vars',
                        'type': 'RESOURCE'
                    },
                    {
                        'name': 'my_resource_two_env_vars',
                        'type': 'RESOURCE'
                    }
                ],
                'envVarName': 'MY_STRING'
            }
        ]
    }
}
