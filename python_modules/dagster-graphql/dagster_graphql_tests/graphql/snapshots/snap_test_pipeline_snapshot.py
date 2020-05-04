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
    "pipelineSnapshotId": "e95e6f29f25ea236ce191a1e8b49ae8601a0afef",
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
    "pipelineSnapshotId": "e95e6f29f25ea236ce191a1e8b49ae8601a0afef",
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_by_snapshot_id_success[create_ephemeral_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
    "pipelineSnapshotId": "e95e6f29f25ea236ce191a1e8b49ae8601a0afef",
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_by_snapshot_id_success[create_local_temp_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
    "pipelineSnapshotId": "e95e6f29f25ea236ce191a1e8b49ae8601a0afef",
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_by_snapshot_id_snapshot_not_found[create_ephemeral_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
  }
}'''

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_by_snapshot_id_snapshot_not_found[create_local_temp_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
  }
}'''

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_by_active_pipeline_name_success[create_ephemeral_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "csv_hello_world",
    "pipelineSnapshotId": "d21414f48707616b77d78a4151b4dc90b0f5406e",
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
        "key": "PoorMansDataFrame"
      },
      {
        "key": "String"
      }
    ],
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_by_active_pipeline_name_success[create_local_temp_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "csv_hello_world",
    "pipelineSnapshotId": "d21414f48707616b77d78a4151b4dc90b0f5406e",
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
        "key": "PoorMansDataFrame"
      },
      {
        "key": "String"
      }
    ],
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

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_by_active_pipeline_name_not_found[create_ephemeral_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineNotFoundError"
  }
}'''

snapshots['TestPipelineSnapshotGraphQL.test_fetch_snapshot_or_error_by_active_pipeline_name_not_found[create_local_temp_instance] 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineNotFoundError"
  }
}'''
