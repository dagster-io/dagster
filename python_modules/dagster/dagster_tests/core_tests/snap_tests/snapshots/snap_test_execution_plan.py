# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_create_execution_plan_with_dep 1'] = '''{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": true,
  "pipeline_snapshot_id": "4ea215f1d60dcf5a758026c8f40f5a7414cb4500",
  "step_keys_to_execute": [
    "solid_one",
    "solid_two"
  ],
  "steps": [
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [],
      "key": "solid_one",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Any",
          "name": "result"
        }
      ],
      "solid_handle_id": "solid_one"
    },
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [
        {
          "__class__": "ExecutionStepInputSnap",
          "dagster_type_key": "Any",
          "name": "num",
          "upstream_output_handles": [
            {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "result",
              "step_key": "solid_one"
            }
          ]
        }
      ],
      "key": "solid_two",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Any",
          "name": "result"
        }
      ],
      "solid_handle_id": "solid_two"
    }
  ]
}'''

snapshots['test_create_noop_execution_plan 1'] = '''{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": true,
  "pipeline_snapshot_id": "d342338a59e11a7d7f4c0de7946f86a9dfb6ef8a",
  "step_keys_to_execute": [
    "noop_solid"
  ],
  "steps": [
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [],
      "key": "noop_solid",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Any",
          "name": "result"
        }
      ],
      "solid_handle_id": "noop_solid"
    }
  ]
}'''

snapshots['test_create_noop_execution_plan_with_tags 1'] = '''{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": true,
  "pipeline_snapshot_id": "3686d4044ac1f1cb178778a75c4dcc88a638ba2a",
  "step_keys_to_execute": [
    "noop_solid"
  ],
  "steps": [
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [],
      "key": "noop_solid",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [
        {
          "__class__": "ExecutionPlanMetadataItemSnap",
          "key": "bar",
          "value": "baaz"
        },
        {
          "__class__": "ExecutionPlanMetadataItemSnap",
          "key": "foo",
          "value": "bar"
        }
      ],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Any",
          "name": "result"
        }
      ],
      "solid_handle_id": "noop_solid"
    }
  ]
}'''

snapshots['test_create_with_composite 1'] = '''{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": true,
  "pipeline_snapshot_id": "3aa03b1e7345952c4dd1ff7907112f70375ebeb4",
  "step_keys_to_execute": [
    "comp_1.return_one",
    "comp_1.add_one",
    "comp_2.return_one",
    "comp_2.add_one",
    "add"
  ],
  "steps": [
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [
        {
          "__class__": "ExecutionStepInputSnap",
          "dagster_type_key": "Any",
          "name": "num_one",
          "upstream_output_handles": [
            {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "result",
              "step_key": "comp_1.add_one"
            }
          ]
        },
        {
          "__class__": "ExecutionStepInputSnap",
          "dagster_type_key": "Any",
          "name": "num_two",
          "upstream_output_handles": [
            {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "result",
              "step_key": "comp_2.add_one"
            }
          ]
        }
      ],
      "key": "add",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Any",
          "name": "result"
        }
      ],
      "solid_handle_id": "add"
    },
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [
        {
          "__class__": "ExecutionStepInputSnap",
          "dagster_type_key": "Int",
          "name": "num",
          "upstream_output_handles": [
            {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "out_num",
              "step_key": "comp_1.return_one"
            }
          ]
        }
      ],
      "key": "comp_1.add_one",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Int",
          "name": "result"
        }
      ],
      "solid_handle_id": "comp_1.add_one"
    },
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [],
      "key": "comp_1.return_one",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Int",
          "name": "out_num"
        }
      ],
      "solid_handle_id": "comp_1.return_one"
    },
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [
        {
          "__class__": "ExecutionStepInputSnap",
          "dagster_type_key": "Int",
          "name": "num",
          "upstream_output_handles": [
            {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "out_num",
              "step_key": "comp_2.return_one"
            }
          ]
        }
      ],
      "key": "comp_2.add_one",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Int",
          "name": "result"
        }
      ],
      "solid_handle_id": "comp_2.add_one"
    },
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [],
      "key": "comp_2.return_one",
      "kind": {
        "__enum__": "StepKind.COMPUTE"
      },
      "metadata_items": [],
      "outputs": [
        {
          "__class__": "ExecutionStepOutputSnap",
          "dagster_type_key": "Int",
          "name": "out_num"
        }
      ],
      "solid_handle_id": "comp_2.return_one"
    }
  ]
}'''
