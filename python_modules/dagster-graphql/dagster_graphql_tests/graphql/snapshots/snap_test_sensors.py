# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestSensors.test_get_sensor[readonly_in_memory_instance_in_process_env] 1'] = {
    '__typename': 'Sensor',
    'id': 'always_no_config_sensor:no_config_pipeline',
    'mode': 'default',
    'name': 'always_no_config_sensor',
    'nextTick': None,
    'pipelineName': 'no_config_pipeline',
    'sensorState': {
        'runs': [
        ],
        'runsCount': 0,
        'status': 'STOPPED',
        'ticks': [
        ]
    },
    'solidSelection': None
}

snapshots['TestSensors.test_get_sensors[readonly_in_memory_instance_in_process_env] 1'] = [
    {
        'id': 'always_no_config_sensor:no_config_pipeline',
        'mode': 'default',
        'name': 'always_no_config_sensor',
        'pipelineName': 'no_config_pipeline',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'solidSelection': None
    },
    {
        'id': 'multi_no_config_sensor:no_config_pipeline',
        'mode': 'default',
        'name': 'multi_no_config_sensor',
        'pipelineName': 'no_config_pipeline',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'solidSelection': None
    },
    {
        'id': 'never_no_config_sensor:no_config_pipeline',
        'mode': 'default',
        'name': 'never_no_config_sensor',
        'pipelineName': 'no_config_pipeline',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'solidSelection': None
    },
    {
        'id': 'once_no_config_sensor:no_config_pipeline',
        'mode': 'default',
        'name': 'once_no_config_sensor',
        'pipelineName': 'no_config_pipeline',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'solidSelection': None
    }
]
