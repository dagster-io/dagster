# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_create_noop_execution_plan 1'] = '''{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": false,
  "pipeline_snapshot_id": "5477a4bd4f8161b7ec6c72c54ca64196f25c8375",
  "step_keys_to_execute": [
    "noop_solid.compute"
  ],
  "steps": [
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [],
      "key": "noop_solid.compute",
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

snapshots['test_create_execution_plan_with_dep 1'] = '''{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": false,
  "pipeline_snapshot_id": "b2dd058376d87ebf542b5b7cfaf0147812bc5dc7",
  "step_keys_to_execute": [
    "solid_one.compute",
    "solid_two.compute"
  ],
  "steps": [
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [],
      "key": "solid_one.compute",
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
              "output_name": "result",
              "step_key": "solid_one.compute"
            }
          ]
        }
      ],
      "key": "solid_two.compute",
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

snapshots['test_create_with_composite 1'] = '''{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": false,
  "pipeline_snapshot_id": "d129f62ffe58f1c9ba4655c14ba37f47cd6e47e3",
  "step_keys_to_execute": [
    "comp_1.return_one.compute",
    "comp_1.add_one.compute",
    "comp_2.return_one.compute",
    "comp_2.add_one.compute",
    "add.compute"
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
              "output_name": "result",
              "step_key": "comp_1.add_one.compute"
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
              "output_name": "result",
              "step_key": "comp_2.add_one.compute"
            }
          ]
        }
      ],
      "key": "add.compute",
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
              "output_name": "out_num",
              "step_key": "comp_1.return_one.compute"
            }
          ]
        }
      ],
      "key": "comp_1.add_one.compute",
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
      "key": "comp_1.return_one.compute",
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
              "output_name": "out_num",
              "step_key": "comp_2.return_one.compute"
            }
          ]
        }
      ],
      "key": "comp_2.add_one.compute",
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
      "key": "comp_2.return_one.compute",
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

snapshots['test_create_noop_execution_plan_with_tags 1'] = '''{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": false,
  "pipeline_snapshot_id": "672b802381d5cced7964e8c95fa535d0d79cab6e",
  "step_keys_to_execute": [
    "noop_solid.compute"
  ],
  "steps": [
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [],
      "key": "noop_solid.compute",
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
