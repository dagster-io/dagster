# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestSensors.test_get_sensors[non_launchable_postgres_instance_lazy_repository] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_error_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 60,
        'name': 'custom_interval_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'dynamic_partition_requesting_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'dynamic_partitioned_assets_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'fresh_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'logging_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'many_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'multi_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'never_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'once_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'run_status',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'running_in_code_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'RUNNING',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'single_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'the_failure_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'update_cursor_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    }
]

snapshots['TestSensors.test_get_sensors[non_launchable_postgres_instance_managed_grpc_env] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_error_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 60,
        'name': 'custom_interval_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'dynamic_partition_requesting_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'dynamic_partitioned_assets_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'fresh_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'logging_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'many_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'multi_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'never_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'once_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'run_status',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'running_in_code_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'RUNNING',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'single_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'the_failure_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'update_cursor_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    }
]

snapshots['TestSensors.test_get_sensors[non_launchable_postgres_instance_multi_location] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_error_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 60,
        'name': 'custom_interval_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'dynamic_partition_requesting_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'dynamic_partitioned_assets_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'fresh_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'logging_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'many_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'multi_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'never_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'once_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'run_status',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'running_in_code_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'RUNNING',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'single_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'the_failure_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'update_cursor_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    }
]

snapshots['TestSensors.test_get_sensors[non_launchable_sqlite_instance_deployed_grpc_env] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_error_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 60,
        'name': 'custom_interval_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'dynamic_partition_requesting_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'dynamic_partitioned_assets_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'fresh_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'logging_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'many_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'multi_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'never_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'once_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'run_status',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'running_in_code_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'RUNNING',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'single_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'the_failure_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'update_cursor_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    }
]

snapshots['TestSensors.test_get_sensors[non_launchable_sqlite_instance_lazy_repository] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_error_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 60,
        'name': 'custom_interval_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'dynamic_partition_requesting_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'dynamic_partitioned_assets_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'fresh_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'logging_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'many_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'multi_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'never_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'once_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'run_status',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'running_in_code_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'RUNNING',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'single_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'the_failure_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'update_cursor_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    }
]

snapshots['TestSensors.test_get_sensors[non_launchable_sqlite_instance_managed_grpc_env] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_error_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 60,
        'name': 'custom_interval_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'dynamic_partition_requesting_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'dynamic_partitioned_assets_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'fresh_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'logging_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'many_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'multi_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'never_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'once_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'run_status',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'running_in_code_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'RUNNING',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'single_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'the_failure_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'update_cursor_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    }
]

snapshots['TestSensors.test_get_sensors[non_launchable_sqlite_instance_multi_location] 1'] = [
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_error_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'always_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 60,
        'name': 'custom_interval_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'dynamic_partition_requesting_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'dynamic_partitioned_assets_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'fresh_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'logging_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'many_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'multi_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'never_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'once_no_config_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'run_status',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'running_in_code_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'RUNNING',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'single_asset_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'single_asset_job',
                'solidSelection': None
            }
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'the_failure_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
        ]
    },
    {
        'description': None,
        'minIntervalSeconds': 30,
        'name': 'update_cursor_sensor',
        'sensorState': {
            'runs': [
            ],
            'runsCount': 0,
            'status': 'STOPPED',
            'ticks': [
            ]
        },
        'targets': [
            {
                'mode': 'default',
                'pipelineName': 'no_config_job',
                'solidSelection': None
            }
        ]
    }
]
