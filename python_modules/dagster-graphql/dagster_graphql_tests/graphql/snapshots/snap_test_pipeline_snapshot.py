# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_fetch_snapshot_or_error_by_snapshot_id_snapshot_not_found 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
  }
}'''

snapshots['test_fetch_snapshot_or_error_by_active_pipeline_name_not_found 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineNotFoundError"
  }
}'''

snapshots['test_fetch_snapshot_or_error_by_snapshot_id_success 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "dagsterTypes": [
      {
        "key": "Any"
      },
      {
        "key": "Bool"
      },
      {
        "key": "Float"
      },
      {
        "key": "Int"
      },
      {
        "key": "Nothing"
      },
      {
        "key": "String"
      }
    ],
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
    "pipelineSnapshotId": "1c2b11984311606d105ccf19239e31d825bd5ba7",
    "solidHandles": [
      {
        "handleID": "noop_solid"
      }
    ],
    "solids": [
      {
        "name": "noop_solid"
      }
    ],
    "tags": []
  }
}'''

snapshots['test_fetch_snapshot_or_error_by_active_pipeline_name_success 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "dagsterTypes": [
      {
        "key": "Any"
      },
      {
        "key": "Bool"
      },
      {
        "key": "Float"
      },
      {
        "key": "Int"
      },
      {
        "key": "Nothing"
      },
      {
        "key": "PoorMansDataFrame"
      },
      {
        "key": "String"
      }
    ],
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "csv_hello_world",
    "pipelineSnapshotId": "9a51b2a71e7e0de6514c4c35cb01af1e79e1b065",
    "solidHandles": [
      {
        "handleID": "sum_solid"
      },
      {
        "handleID": "sum_sq_solid"
      }
    ],
    "solids": [
      {
        "name": "sum_solid"
      },
      {
        "name": "sum_sq_solid"
      }
    ],
    "tags": []
  }
}'''
