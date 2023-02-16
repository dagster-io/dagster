# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_create_with_graph 1"
] = """{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": true,
  "executor_name": "multi_or_in_process_executor",
  "initial_known_state": {
    "__class__": "KnownExecutionState",
    "dynamic_mappings": {},
    "parent_state": null,
    "previous_retry_attempts": {},
    "ready_outputs": {
      "__frozenset__": []
    },
    "step_output_versions": []
  },
  "pipeline_snapshot_id": "9fbbf986b4eac313bbfdb3b47416b203791730a8",
  "snapshot_version": 1,
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
          "source": {
            "__class__": "FromStepOutput",
            "fan_in": false,
            "input_name": "",
            "solid_handle": {
              "__class__": "SolidHandle",
              "name": "",
              "parent": null
            },
            "step_output_handle": {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "result",
              "step_key": "comp_1.add_one"
            }
          },
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
          "source": {
            "__class__": "FromStepOutput",
            "fan_in": false,
            "input_name": "",
            "solid_handle": {
              "__class__": "SolidHandle",
              "name": "",
              "parent": null
            },
            "step_output_handle": {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "result",
              "step_key": "comp_2.add_one"
            }
          },
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
          "name": "result",
          "properties": {
            "__class__": "StepOutputProperties",
            "asset_key": null,
            "is_asset": false,
            "is_dynamic": false,
            "is_required": true,
            "should_materialize": false
          },
          "solid_handle": {
            "__class__": "SolidHandle",
            "name": "add",
            "parent": null
          }
        }
      ],
      "solid_handle_id": "add",
      "step_handle": {
        "__class__": "StepHandle",
        "key": "add",
        "solid_handle": {
          "__class__": "SolidHandle",
          "name": "add",
          "parent": null
        }
      },
      "tags": {}
    },
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [
        {
          "__class__": "ExecutionStepInputSnap",
          "dagster_type_key": "Int",
          "name": "num",
          "source": {
            "__class__": "FromStepOutput",
            "fan_in": false,
            "input_name": "",
            "solid_handle": {
              "__class__": "SolidHandle",
              "name": "",
              "parent": null
            },
            "step_output_handle": {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "out_num",
              "step_key": "comp_1.return_one"
            }
          },
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
          "name": "result",
          "properties": {
            "__class__": "StepOutputProperties",
            "asset_key": null,
            "is_asset": false,
            "is_dynamic": false,
            "is_required": true,
            "should_materialize": false
          },
          "solid_handle": {
            "__class__": "SolidHandle",
            "name": "add_one",
            "parent": {
              "__class__": "SolidHandle",
              "name": "comp_1",
              "parent": null
            }
          }
        }
      ],
      "solid_handle_id": "comp_1.add_one",
      "step_handle": {
        "__class__": "StepHandle",
        "key": "comp_1.add_one",
        "solid_handle": {
          "__class__": "SolidHandle",
          "name": "add_one",
          "parent": {
            "__class__": "SolidHandle",
            "name": "comp_1",
            "parent": null
          }
        }
      },
      "tags": {}
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
          "name": "out_num",
          "properties": {
            "__class__": "StepOutputProperties",
            "asset_key": null,
            "is_asset": false,
            "is_dynamic": false,
            "is_required": true,
            "should_materialize": false
          },
          "solid_handle": {
            "__class__": "SolidHandle",
            "name": "return_one",
            "parent": {
              "__class__": "SolidHandle",
              "name": "comp_1",
              "parent": null
            }
          }
        }
      ],
      "solid_handle_id": "comp_1.return_one",
      "step_handle": {
        "__class__": "StepHandle",
        "key": "comp_1.return_one",
        "solid_handle": {
          "__class__": "SolidHandle",
          "name": "return_one",
          "parent": {
            "__class__": "SolidHandle",
            "name": "comp_1",
            "parent": null
          }
        }
      },
      "tags": {}
    },
    {
      "__class__": "ExecutionStepSnap",
      "inputs": [
        {
          "__class__": "ExecutionStepInputSnap",
          "dagster_type_key": "Int",
          "name": "num",
          "source": {
            "__class__": "FromStepOutput",
            "fan_in": false,
            "input_name": "",
            "solid_handle": {
              "__class__": "SolidHandle",
              "name": "",
              "parent": null
            },
            "step_output_handle": {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "out_num",
              "step_key": "comp_2.return_one"
            }
          },
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
          "name": "result",
          "properties": {
            "__class__": "StepOutputProperties",
            "asset_key": null,
            "is_asset": false,
            "is_dynamic": false,
            "is_required": true,
            "should_materialize": false
          },
          "solid_handle": {
            "__class__": "SolidHandle",
            "name": "add_one",
            "parent": {
              "__class__": "SolidHandle",
              "name": "comp_2",
              "parent": null
            }
          }
        }
      ],
      "solid_handle_id": "comp_2.add_one",
      "step_handle": {
        "__class__": "StepHandle",
        "key": "comp_2.add_one",
        "solid_handle": {
          "__class__": "SolidHandle",
          "name": "add_one",
          "parent": {
            "__class__": "SolidHandle",
            "name": "comp_2",
            "parent": null
          }
        }
      },
      "tags": {}
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
          "name": "out_num",
          "properties": {
            "__class__": "StepOutputProperties",
            "asset_key": null,
            "is_asset": false,
            "is_dynamic": false,
            "is_required": true,
            "should_materialize": false
          },
          "solid_handle": {
            "__class__": "SolidHandle",
            "name": "return_one",
            "parent": {
              "__class__": "SolidHandle",
              "name": "comp_2",
              "parent": null
            }
          }
        }
      ],
      "solid_handle_id": "comp_2.return_one",
      "step_handle": {
        "__class__": "StepHandle",
        "key": "comp_2.return_one",
        "solid_handle": {
          "__class__": "SolidHandle",
          "name": "return_one",
          "parent": {
            "__class__": "SolidHandle",
            "name": "comp_2",
            "parent": null
          }
        }
      },
      "tags": {}
    }
  ]
}"""
