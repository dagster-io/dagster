# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_success[create_ephemeral_instance] 1'] = '''{
  "pipelineSnapshot": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
    "pipelineSnapshotId": "88528edde2ed64da3c39cca0da8ba2f7586c1a5d",
    "runtimeTypes": [
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
        "key": "Path"
      },
      {
        "key": "String"
      }
    ],
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_success[create_local_temp_instance] 1'] = '''{
  "pipelineSnapshot": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
    "pipelineSnapshotId": "88528edde2ed64da3c39cca0da8ba2f7586c1a5d",
    "runtimeTypes": [
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
        "key": "Path"
      },
      {
        "key": "String"
      }
    ],
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_success[create_ephemeral_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
    "pipelineSnapshotId": "88528edde2ed64da3c39cca0da8ba2f7586c1a5d",
    "runtimeTypes": [
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
        "key": "Path"
      },
      {
        "key": "String"
      }
    ],
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_success[create_local_temp_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
    "pipelineSnapshotId": "88528edde2ed64da3c39cca0da8ba2f7586c1a5d",
    "runtimeTypes": [
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
        "key": "Path"
      },
      {
        "key": "String"
      }
    ],
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_snapshot_not_found[create_ephemeral_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
  }
}'''

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_snapshot_not_found[create_local_temp_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
  }
}'''
