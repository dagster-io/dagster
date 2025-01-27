import pytest
from dagster import job
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot
from dagster._serdes.serdes import deserialize_value

OLD_EXECUTION_PLAN_SNAPSHOT = """{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": true,
  "initial_known_state": null,
  "pipeline_snapshot_id": "0baebbaa257331ddeaccd3076c3dca413e099cf4",
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
          "name": "result",
          "properties": {
            "__class__": "StepOutputProperties",
            "is_asset": false,
            "is_dynamic": false,
            "is_required": true,
            "should_materialize": false
          },
          "solid_handle": {
            "__class__": "SolidHandle",
            "name": "solid_one",
            "parent": null
          }
        }
      ],
      "solid_handle_id": "solid_one",
      "step_handle": {
        "__class__": "StepHandle",
        "solid_handle": {
          "__class__": "SolidHandle",
          "name": "solid_one",
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
          "dagster_type_key": "Any",
          "name": "num",
          "source": {
            "__class__": "FromStepOutput",
            "fan_in": false,
            "input_name": "num",
            "solid_handle": {
              "__class__": "SolidHandle",
              "name": "solid_two",
              "parent": null
            },
            "step_output_handle": {
              "__class__": "StepOutputHandle",
              "mapping_key": null,
              "output_name": "result",
              "step_key": "solid_one"
            }
          },
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
          "name": "result",
          "properties": {
            "__class__": "StepOutputProperties",
            "is_asset": false,
            "is_dynamic": false,
            "is_required": true,
            "should_materialize": false
          },
          "solid_handle": {
            "__class__": "SolidHandle",
            "name": "solid_two",
            "parent": null
          }
        }
      ],
      "solid_handle_id": "solid_two",
      "step_handle": {
        "__class__": "StepHandle",
        "solid_handle": {
          "__class__": "SolidHandle",
          "name": "solid_two",
          "parent": null
        }
      },
      "tags": {}
    }
  ]
}"""


@job
def noop_job():
    pass


def test_cant_load_old_snapshot():
    snapshot = deserialize_value(OLD_EXECUTION_PLAN_SNAPSHOT, ExecutionPlanSnapshot)
    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Tried to reconstruct an old ExecutionPlanSnapshot that was created before snapshots"
            " had enough information to fully reconstruct the ExecutionPlan"
        ),
    ):
        ExecutionPlan.rebuild_from_snapshot("noop_job", snapshot)


PRE_CACHE_EXECUTION_PLAN_SNAPSHOT = """{
  "__class__": "ExecutionPlanSnapshot",
  "artifacts_persisted": true,
  "initial_known_state": null,
  "pipeline_snapshot_id": "0965b76124e758660317760c7e9bbc66282f33b0",
  "snapshot_version": 1,
  "step_keys_to_execute": [
    "noop_solid"
  ],
  "step_output_versions": [],
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
          "name": "result",
          "properties": {
            "__class__": "StepOutputProperties",
            "is_asset": false,
            "is_dynamic": false,
            "is_required": true,
            "should_materialize": false
          },
          "solid_handle": {
            "__class__": "SolidHandle",
            "name": "noop_solid",
            "parent": null
          }
        }
      ],
      "solid_handle_id": "noop_solid",
      "step_handle": {
        "__class__": "StepHandle",
        "solid_handle": {
          "__class__": "SolidHandle",
          "name": "noop_solid",
          "parent": null
        }
      },
      "tags": {}
    }
  ]
}"""


def test_rebuild_pre_cached_key_execution_plan_snapshot():
    snapshot = deserialize_value(PRE_CACHE_EXECUTION_PLAN_SNAPSHOT, ExecutionPlanSnapshot)
    ExecutionPlan.rebuild_from_snapshot("noop_job", snapshot)
