# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots[
    'TestExecuteSchedule.test_tick_skip[sqlite_with_default_run_launcher_in_process_env] 1'
] = {
    'stats': {'ticksFailed': 0, 'ticksSkipped': 1, 'ticksStarted': 0, 'ticksSucceeded': 0},
    'ticks': [{'status': 'SKIPPED', 'tickId': '1'}],
    'ticksCount': 1,
}

snapshots[
    'TestExecuteSchedule.test_tick_success[sqlite_with_default_run_launcher_in_process_env] 1'
] = {
    'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 1},
    'ticks': [{'status': 'SUCCESS', 'tickId': '1'}],
    'ticksCount': 1,
}

snapshots[
    'TestExecuteSchedule.test_should_execute_scheduler_error[sqlite_with_default_run_launcher_in_process_env] 1'
] = {
    'stats': {'ticksFailed': 1, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
    'ticks': [{'status': 'FAILURE', 'tickId': '1'}],
    'ticksCount': 1,
}

snapshots[
    'TestExecuteSchedule.test_tags_scheduler_error[sqlite_with_default_run_launcher_in_process_env] 1'
] = {
    'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 1},
    'ticks': [{'status': 'SUCCESS', 'tickId': '1'}],
    'ticksCount': 1,
}

snapshots[
    'TestExecuteSchedule.test_run_config_scheduler_error[sqlite_with_default_run_launcher_in_process_env] 1'
] = {
    'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 1},
    'ticks': [{'status': 'SUCCESS', 'tickId': '1'}],
    'ticksCount': 1,
}

snapshots[
    'TestExecuteSchedule.test_query_multiple_schedule_ticks[sqlite_with_default_run_launcher_in_process_env] 1'
] = [
    {
        'name': 'dynamic_config',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'run_config_error_schedule',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 1},
            'ticks': [{'status': 'SUCCESS', 'tickId': '3'}],
            'ticksCount': 1,
        },
    },
    {
        'name': 'invalid_config_schedule',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'no_config_pipeline_hourly_schedule',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 1},
            'ticks': [{'status': 'SUCCESS', 'tickId': '1'}],
            'ticksCount': 1,
        },
    },
    {
        'name': 'no_config_pipeline_hourly_schedule_with_config_fn',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'no_config_should_execute',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 1, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [{'status': 'SKIPPED', 'tickId': '2'}],
            'ticksCount': 1,
        },
    },
    {
        'name': 'partition_based',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'partition_based_custom_selector',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'partition_based_decorator',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'partition_based_multi_mode_decorator',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'should_execute_error_schedule',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'solid_selection_daily_decorator',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'solid_selection_hourly_decorator',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'solid_selection_monthly_decorator',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'solid_selection_weekly_decorator',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'tagged_pipeline_override_schedule',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'tagged_pipeline_schedule',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
    {
        'name': 'tags_error_schedule',
        'scheduleState': {
            'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 0},
            'ticks': [],
            'ticksCount': 0,
        },
    },
]

snapshots[
    'TestExecuteSchedule.test_invalid_config_schedule_error[sqlite_with_default_run_launcher_in_process_env] 1'
] = {
    'stats': {'ticksFailed': 0, 'ticksSkipped': 0, 'ticksStarted': 0, 'ticksSucceeded': 1},
    'ticks': [{'status': 'SUCCESS', 'tickId': '1'}],
    'ticksCount': 1,
}
