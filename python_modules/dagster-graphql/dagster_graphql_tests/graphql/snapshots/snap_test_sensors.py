# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestSensors.test_get_sensor[non_launchable_in_memory_instance_lazy_repository] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_in_memory_instance_managed_grpc_env] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_in_memory_instance_multi_location] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_postgres_instance_lazy_repository] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_postgres_instance_managed_grpc_env] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_postgres_instance_multi_location] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_sqlite_instance_lazy_repository] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_sqlite_instance_managed_grpc_env] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensor[non_launchable_sqlite_instance_multi_location] 1'] = {
    '__typename': 'Sensor',
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

snapshots['TestSensors.test_get_sensors[non_launchable_in_memory_instance_lazy_repository] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_in_memory_instance_managed_grpc_env] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_in_memory_instance_multi_location] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_postgres_instance_lazy_repository] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_postgres_instance_managed_grpc_env] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_postgres_instance_multi_location] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_sqlite_instance_lazy_repository] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_sqlite_instance_managed_grpc_env] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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

snapshots['TestSensors.test_get_sensors[non_launchable_sqlite_instance_multi_location] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 60,
        'mode': 'default',
        'name': 'custom_interval_sensor',
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
        'description': None,
        'minIntervalSeconds': 30,
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
