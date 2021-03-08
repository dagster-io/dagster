# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_instance_yaml 1'] = [
    'compute_logs',
    'event_log_storage',
    'local_artifact_storage',
    'run_coordinator',
    'run_launcher',
    'run_storage',
    'schedule_storage',
    'scheduler',
    'telemetry'
]
