from dagster import check
from dagster.core.events import DagsterEvent
from dagster.core.execution.plan.objects import StepSuccessData
from dagster_k8s import utils


def test_filter_dagster_events_from_pod_logs():

    sameple_output = """
    2020-07-17 11:31:58 - dagster - DEBUG - foo - new_run - STEP_START - Started execution of step "do_something".
                 pid = 2467
               solid = "do_something"
    solid_definition = "do_something"
            step_key = "do_something"
{"__class__": "DagsterEvent", "event_specific_data": null, "event_type_value": "STEP_START", "logging_tags": {"pipeline": "foo", "solid": "do_something", "solid_definition": "do_something", "step_key": "do_something"}, "message": "Started execution of step \\"do_something.compute\\".", "pid": 2467, "pipeline_name": "foo", "solid_handle": {"__class__": "SolidHandle", "name": "do_something", "parent": null}, "step_key": "do_something", "step_kind_value": "COMPUTE"}
2020-07-17 11:31:58 - dagster - DEBUG - foo - new_run - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
 event_specific_data = {"intermediate_materialization": null, "step_output_handle": ["do_something", "result"], "type_check_data": [true, "result", null, []]}
                 pid = 2467
               solid = "do_something"
    solid_definition = "do_something"
            step_key = "do_something"
{"__class__": "DagsterEvent", "event_specific_data": {"__class__": "StepOutputData", "intermediate_materialization": null, "step_output_handle": {"__class__": "StepOutputHandle", "output_name": "result", "step_key": "do_something"}, "type_check_data": {"__class__": "TypeCheckData", "description": null, "label": "result", "metadata_entries": [], "success": true}}, "event_type_value": "STEP_OUTPUT", "logging_tags": {"pipeline": "foo", "solid": "do_something", "solid_definition": "do_something", "step_key": "do_something"}, "message": "Yielded output \\"result\\" of type \\"Any\\". (Type check passed).", "pid": 2467, "pipeline_name": "foo", "solid_handle": {"__class__": "SolidHandle", "name": "do_something", "parent": null}, "step_key": "do_something", "step_kind_value": "COMPUTE"}
2020-07-17 11:31:58 - dagster - DEBUG - foo - new_run - STEP_SUCCESS - Finished execution of step "do_something" in 13ms.
 event_specific_data = {"duration_ms": 13.93123900000015}
                 pid = 2467
               solid = "do_something"
    solid_definition = "do_something"
            step_key = "do_something"
{"__class__": "DagsterEvent", "event_specific_data": {"__class__": "StepSuccessData", "duration_ms": 13.93123900000015}, "event_type_value": "STEP_SUCCESS", "logging_tags": {"pipeline": "foo", "solid": "do_something", "solid_definition": "do_something", "step_key": "do_something"}, "message": "Finished execution of step \\"do_something.compute\\" in 13ms.", "pid": 2467, "pipeline_name": "foo", "solid_handle": {"__class__": "SolidHandle", "name": "do_something", "parent": null}, "step_key": "do_something", "step_kind_value": "COMPUTE"}
2020-07-17 11:31:58 - dagster - DEBUG - foo - new_run - STEP_START - Started execution of step "do_input".
                 pid = 2467
               solid = "do_input"
    solid_definition = "do_input"
            step_key = "do_input"
{"__class__": "DagsterEvent", "event_specific_data": null, "event_type_value": "STEP_START", "logging_tags": {"pipeline": "foo", "solid": "do_input", "solid_definition": "do_input", "step_key": "do_input"}, "message": "Started execution of step \\"do_input.compute\\".", "pid": 2467, "pipeline_name": "foo", "solid_handle": {"__class__": "SolidHandle", "name": "do_input", "parent": null}, "step_key": "do_input", "step_kind_value": "COMPUTE"}
2020-07-17 11:31:58 - dagster - DEBUG - foo - new_run - STEP_INPUT - Got input "x" of type "Any". (Type check passed).
 event_specific_data = {"input_name": "x", "type_check_data": [true, "x", null, []]}
                 pid = 2467
               solid = "do_input"
    solid_definition = "do_input"
            step_key = "do_input"
{"__class__": "DagsterEvent", "event_specific_data": {"__class__": "StepInputData", "input_name": "x", "type_check_data": {"__class__": "TypeCheckData", "description": null, "label": "x", "metadata_entries": [], "success": true}}, "event_type_value": "STEP_INPUT", "logging_tags": {"pipeline": "foo", "solid": "do_input", "solid_definition": "do_input", "step_key": "do_input"}, "message": "Got input \\"x\\" of type \\"Any\\". (Type check passed).", "pid": 2467, "pipeline_name": "foo", "solid_handle": {"__class__": "SolidHandle", "name": "do_input", "parent": null}, "step_key": "do_input", "step_kind_value": "COMPUTE"}
2020-07-17 11:31:58 - dagster - DEBUG - foo - new_run - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
 event_specific_data = {"intermediate_materialization": null, "step_output_handle": ["do_input", "result"], "type_check_data": [true, "result", null, []]}
                 pid = 2467
               solid = "do_input"
    solid_definition = "do_input"
            step_key = "do_input"
{"__class__": "DagsterEvent", "event_specific_data": {"__class__": "StepOutputData", "intermediate_materialization": null, "step_output_handle": {"__class__": "StepOutputHandle", "output_name": "result", "step_key": "do_input"}, "type_check_data": {"__class__": "TypeCheckData", "description": null, "label": "result", "metadata_entries": [], "success": true}}, "event_type_value": "STEP_OUTPUT", "logging_tags": {"pipeline": "foo", "solid": "do_input", "solid_definition": "do_input", "step_key": "do_input"}, "message": "Yielded output \\"result\\" of type \\"Any\\". (Type check passed).", "pid": 2467, "pipeline_name": "foo", "solid_handle": {"__class__": "SolidHandle", "name": "do_input", "parent": null}, "step_key": "do_input", "step_kind_value": "COMPUTE"}
2020-07-17 11:31:58 - dagster - DEBUG - foo - new_run - STEP_SUCCESS - Finished execution of step "do_input" in 13ms.
 event_specific_data = {"duration_ms": 13.923579000000075}
                 pid = 2467
               solid = "do_input"
    solid_definition = "do_input"
            step_key = "do_input"
{"__class__": "DagsterEvent", "event_specific_data": {"__class__": "StepSuccessData", "duration_ms": 13.923579000000075}, "event_type_value": "STEP_SUCCESS", "logging_tags": {"pipeline": "foo", "solid": "do_input", "solid_definition": "do_input", "step_key": "do_input"}, "message": "Finished execution of step \\"do_input.compute\\" in 13ms.", "pid": 2467, "pipeline_name": "foo", "solid_handle": {"__class__": "SolidHandle", "name": "do_input", "parent": null}, "step_key": "do_input", "step_kind_value": "COMPUTE"}
""".split(
        "\n"
    )
    res = utils.filter_dagster_events_from_pod_logs(sameple_output)

    assert len(res) == 7

    last_event = res[-1]
    check.inst(last_event, DagsterEvent)
    check.inst(last_event.event_specific_data, StepSuccessData)


def test_filter_dagster_events_from_pod_logs_coalesce():
    logs = """
    {"__class__": "DagsterEvent", "event_specific
    _data": {"__class__": "StepSuccessData", "duration_ms": 13.923579000000075}, "event_typ
    e_value": "STEP_SUCCESS", "logging_tags": {"pipeline": "foo", "so
    lid": "do_input", "solid_definition": "do_input", "step_key": "do_input"}, "message": "Finished execution of step \\"do_input.compute\\" in 13ms.", "pid": 2467, "pipeline_name": "foo", "solid_handle": {"__class__": "SolidHandle", "name": "do_input", "parent": null}, "step_key": "do_input", "step_kind_value": "COMPUTE"}
    """.split(
        "\n"
    )
    res = utils.filter_dagster_events_from_pod_logs(logs)
    assert len(res) == 1

    event = res[0]
    check.inst(event, DagsterEvent)
    check.inst(event.event_specific_data, StepSuccessData)
