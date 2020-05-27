# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_pipeline_reexecution_info_query 1'] = [
    'sum_sq_solid.compute'
]

snapshots['TestRetryExecution.test_pipeline_reexecution_info_query[sqlite_in_process_start] 1'] = [
    'sum_sq_solid.compute'
]

snapshots['TestRetryExecution.test_pipeline_reexecution_info_query[in_memory_in_process_start] 1'] = [
    'sum_sq_solid.compute'
]

snapshots['TestRetryExecution.test_pipeline_reexecution_info_query[sqlite_subprocess_start] 1'] = [
    'sum_sq_solid.compute'
]

snapshots['TestRetryExecution.test_pipeline_reexecution_info_query[in_memory_instance_with_sync_hijack] 1'] = [
    'sum_sq_solid.compute'
]
