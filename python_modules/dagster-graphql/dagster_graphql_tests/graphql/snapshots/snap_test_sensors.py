# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestSensors.test_get_sensor[non_launchable_sqlite_instance_lazy_repository] 1'] = {
    '__typename': 'Sensor',
    'id': 'always_no_config_sensor:no_config_pipeline',
    'minIntervalSeconds': 30,
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
