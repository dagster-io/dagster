# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()


snapshots[
    'test_fetch_snapshot_or_error_by_snapshot_id_snapshot_not_found 1'
] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
  }
}'''


snapshots[
    'test_fetch_snapshot_or_error_by_active_pipeline_name_not_found 1'
] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineNotFoundError"
  }
}'''
