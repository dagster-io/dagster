# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_query_multiple_schedule_ticks 1'] = [
    {
        'scheduleDefinition': {
            'name': 'dynamic_config'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'environment_dict_error_schedule'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 1
        },
        'ticks': [
            {
                'status': 'SUCCESS',
                'tickId': '3'
            }
        ],
        'ticksCount': 1
    },
    {
        'scheduleDefinition': {
            'name': 'invalid_config_schedule'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'no_config_pipeline_hourly_schedule'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 1
        },
        'ticks': [
            {
                'status': 'SUCCESS',
                'tickId': '1'
            }
        ],
        'ticksCount': 1
    },
    {
        'scheduleDefinition': {
            'name': 'no_config_pipeline_hourly_schedule_with_config_fn'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'no_config_should_execute'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 1,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
            {
                'status': 'SKIPPED',
                'tickId': '2'
            }
        ],
        'ticksCount': 1
    },
    {
        'scheduleDefinition': {
            'name': 'partition_based'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'partition_based_custom_selector'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'partition_based_decorator'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'partition_based_multi_mode_decorator'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'should_execute_error_schedule'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'solid_subset_daily_decorator'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'solid_subset_hourly_decorator'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'solid_subset_monthly_decorator'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'solid_subset_weekly_decorator'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'tagged_pipeline_override_schedule'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'tagged_pipeline_schedule'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    },
    {
        'scheduleDefinition': {
            'name': 'tags_error_schedule'
        },
        'stats': {
            'ticksFailed': 0,
            'ticksSkipped': 0,
            'ticksStarted': 0,
            'ticksSucceeded': 0
        },
        'ticks': [
        ],
        'ticksCount': 0
    }
]

snapshots['test_tick_skip 1'] = {
    'scheduleDefinition': {
        'name': 'no_config_should_execute'
    },
    'stats': {
        'ticksFailed': 0,
        'ticksSkipped': 1,
        'ticksStarted': 0,
        'ticksSucceeded': 0
    },
    'ticks': [
        {
            'status': 'SKIPPED',
            'tickId': '1'
        }
    ],
    'ticksCount': 1
}

snapshots['test_tags_scheduler_error 1'] = {
    'scheduleDefinition': {
        'name': 'tags_error_schedule'
    },
    'stats': {
        'ticksFailed': 0,
        'ticksSkipped': 0,
        'ticksStarted': 0,
        'ticksSucceeded': 1
    },
    'ticks': [
        {
            'status': 'SUCCESS',
            'tickId': '1'
        }
    ],
    'ticksCount': 1
}

snapshots['test_enviornment_dict_scheduler_error 1'] = {
    'scheduleDefinition': {
        'name': 'environment_dict_error_schedule'
    },
    'stats': {
        'ticksFailed': 0,
        'ticksSkipped': 0,
        'ticksStarted': 0,
        'ticksSucceeded': 1
    },
    'ticks': [
        {
            'status': 'SUCCESS',
            'tickId': '1'
        }
    ],
    'ticksCount': 1
}
