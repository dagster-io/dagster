from os import path

from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.serdes import deserialize_json_to_dagster_namedtuple, deserialize_value


def test_dead_events():
    snapshot = path.join(path.dirname(path.realpath(__file__)), "dead_events.txt")
    with open(snapshot, "r") as fd:
        objs = []
        for line in fd.readlines():
            obj = deserialize_value(line)
            assert obj is not None
            objs.append(obj)

    assert len(objs) == 6


def test_dead_pipeline_init_failure_event():
    old_pipeline_init_failure_event = """{"__class__":"EventRecord","dagster_event":{"__class__":"DagsterEvent","event_specific_data":{"__class__":"PipelineFailureData","error":{"__class__":"SerializableErrorInfo","cause":null,"cls_name":"DagsterError","message":"","stack":[]}},"event_type_value":"PIPELINE_FAILURE","logging_tags":{},"message":"Pipeline failure during initialization for pipeline.","pid":16977,"pipeline_name":"error_monster","solid_handle":null,"step_handle":null,"step_key":null,"step_kind_value":null},"error_info":null,"level":40,"message":"error_monster - a52c3489-60ca-4801-bf8d-43d3ebcbf81f - 16977 - PIPELINE_INIT_FAILURE - Pipeline failure during initialization for pipeline.","pipeline_name":"error_monster","run_id":"a52c3489-60ca-4801-bf8d-43d3ebcbf81f","step_key":null,"timestamp":1622868716.203709,"user_message":"Pipeline failure during initialization for pipeline. This may be due to a failure in initializing the executor or one of the loggers."}"""
    event_record = deserialize_json_to_dagster_namedtuple(old_pipeline_init_failure_event)
    old_event = event_record.dagster_event
    assert old_event
    new_event = DagsterEvent(
        event_type_value=old_event.event_type_value,
        pipeline_name=old_event.pipeline_name,
        event_specific_data=old_event.event_specific_data,
    )
    assert new_event.event_type_value == DagsterEventType.PIPELINE_FAILURE.value
    assert new_event.event_specific_data
