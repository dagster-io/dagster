# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_fetch_snapshot_or_error_by_active_pipeline_name_not_found 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineNotFoundError"
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
    "pipelineSnapshotId": "7b00119a72d6eee0e56272eeae130f3794d49c41",
    "solidHandles": [
      {
        "handleID": "sum_op"
      },
      {
        "handleID": "sum_sq_op"
      }
    ],
    "solids": [
      {
        "name": "sum_op"
      },
      {
        "name": "sum_sq_op"
      }
    ],
    "tags": []
  }
}'''

snapshots['test_fetch_snapshot_or_error_by_snapshot_id_snapshot_not_found 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
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
    "name": "noop_job",
    "pipelineSnapshotId": "df3268d8df147690b83b139db3255d7055556039",
    "solidHandles": [
      {
        "handleID": "noop_op"
      }
    ],
    "solids": [
      {
        "name": "noop_op"
      }
    ],
    "tags": []
  }
}'''
