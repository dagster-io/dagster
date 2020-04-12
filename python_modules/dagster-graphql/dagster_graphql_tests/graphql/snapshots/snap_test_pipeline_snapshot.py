# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_query_pipeline_snapshot_empheral_instance 1'] = '''{
  "pipelineSnapshot": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
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

snapshots['test_query_pipeline_snapshot_local_temp_instance 1'] = '''{
  "pipelineSnapshot": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
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

snapshots['test_query_pipeline_snapshot_or_error_empheral_instance 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
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

snapshots['test_query_pipeline_snapshot_or_error_local_temp_instance 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshot",
    "description": null,
    "modes": [
      {
        "name": "default"
      }
    ],
    "name": "noop_pipeline",
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

snapshots['test_query_pipeline_snapshot_or_error_not_found_empheral_instance 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
  }
}'''

snapshots['test_query_pipeline_snapshot_or_error_not_found_local_temp_instance 1'] = '''{
  "pipelineSnapshotOrError": {
    "__typename": "PipelineSnapshotNotFoundError",
    "snapshotId": "notthere"
  }
}'''
