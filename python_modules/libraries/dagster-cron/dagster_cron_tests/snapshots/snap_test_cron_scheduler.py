# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_start_schedule_manual_delete_debug 1'] = (
    [
        'Schedule no_config_pipeline_every_min_schedule is set to be running, but the scheduler is not running the schedule. Run `dagster schedule up` to resolve'
    ],
    '''Scheduler:
     SystemCronScheduler

''',
    '''Running Cron Jobs:

''',
    [
        '''default_config_pipeline_every_min_schedule:
  cron_schedule: '* * * * *'
  python_path: fake path
  repository_name: test_repository
  repository_path: ''
  status: STOPPED
''',
        '''no_config_pipeline_daily_schedule:
  cron_schedule: 0 0 * * *
  python_path: fake path
  repository_name: test_repository
  repository_path: ''
  status: STOPPED
''',
        '''no_config_pipeline_every_min_schedule:
  cron_schedule: '* * * * *'
  python_path: fake path
  repository_name: test_repository
  repository_path: ''
  status: RUNNING
'''
    ]
)
