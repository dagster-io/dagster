from dagster import EventMetadataEntry, check, seven
from dagster.core.definitions import (
    AssetMaterialization,
    ExpectationResult,
    Materialization,
    SolidHandle,
)
from dagster.core.definitions.events import PythonArtifactMetadataEntryData
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    StepExpectationResultData,
    StepMaterializationData,
)
from dagster.core.execution.plan.objects import (
    StepFailureData,
    StepInputData,
    StepOutputData,
    StepOutputHandle,
    StepRetryData,
    StepSuccessData,
    TypeCheckData,
    UserFailureData,
)
from dagster.utils.error import SerializableErrorInfo

HANDLED_EVENTS = {
    "ExecutionStepStartEvent": DagsterEventType.STEP_START,
    "ExecutionStepInputEvent": DagsterEventType.STEP_INPUT,
    "ExecutionStepOutputEvent": DagsterEventType.STEP_OUTPUT,
    "ExecutionStepFailureEvent": DagsterEventType.STEP_FAILURE,
    "ExecutionStepSkippedEvent": DagsterEventType.STEP_SKIPPED,
    "ExecutionStepSuccessEvent": DagsterEventType.STEP_SUCCESS,
    "StepMaterializationEvent": DagsterEventType.STEP_MATERIALIZATION,
    "StepExpectationResultEvent": DagsterEventType.STEP_EXPECTATION_RESULT,
    "ObjectStoreOperationEvent": DagsterEventType.OBJECT_STORE_OPERATION,
    "EngineEvent": DagsterEventType.ENGINE_EVENT,
    "ExecutionStepUpForRetryEvent": DagsterEventType.STEP_UP_FOR_RETRY,
    "ExecutionStepRestartEvent": DagsterEventType.STEP_RESTARTED,
}


def expectation_result_from_data(data):
    return ExpectationResult(
        success=data["success"],
        label=data["label"],
        description=data.get("description"),  # enforce?
        metadata_entries=list(event_metadata_entries(data.get("metadataEntries")) or []),
    )


def materialization_from_data(data):
    if data.get("asset_key"):
        return AssetMaterialization(
            asset_key=data["asset_key"],
            description=data.get("description"),
            metadata_entries=list(event_metadata_entries(data.get("metadataEntries")) or []),
        )
    return Materialization(
        label=data["label"],
        description=data.get("description"),  # enforce?
        metadata_entries=list(event_metadata_entries(data.get("metadataEntries")) or []),
    )


def error_from_data(data):
    return SerializableErrorInfo(
        message=data["message"],
        stack=data["stack"],
        cls_name=data["className"],
        cause=error_from_data(data["cause"]) if data.get("cause") else None,
    )


def event_metadata_entries(metadata_entry_datas):
    if not metadata_entry_datas:
        return

    for metadata_entry_data in metadata_entry_datas:
        typename = metadata_entry_data["__typename"]
        label = metadata_entry_data["label"]
        description = metadata_entry_data.get("description")
        if typename == "EventPathMetadataEntry":
            yield EventMetadataEntry.path(
                label=label, description=description, path=metadata_entry_data["path"]
            )
        elif typename == "EventJsonMetadataEntry":
            yield EventMetadataEntry.json(
                label=label,
                description=description,
                data=seven.json.loads(metadata_entry_data.get("jsonString", "")),
            )
        elif typename == "EventMarkdownMetadataEntry":
            yield EventMetadataEntry.md(
                label=label, description=description, md_str=metadata_entry_data.get("md_str", "")
            )
        elif typename == "EventTextMetadataEntry":
            yield EventMetadataEntry.text(
                label=label, description=description, text=metadata_entry_data["text"]
            )
        elif typename == "EventUrlMetadataEntry":
            yield EventMetadataEntry.url(
                label=label, description=description, url=metadata_entry_data["url"]
            )
        elif typename == "EventPythonArtifactMetadataEntry":
            yield EventMetadataEntry(
                label=label,
                description=description,
                entry_data=PythonArtifactMetadataEntryData(
                    metadata_entry_data["module"], metadata_entry_data["name"]
                ),
            )
        else:
            check.not_implemented("TODO for type {}".format(typename))


def dagster_event_from_dict(event_dict, pipeline_name):
    check.dict_param(event_dict, "event_dict", key_type=str)
    check.str_param(pipeline_name, "pipeline_name")

    # Get event_type
    event_type = HANDLED_EVENTS.get(event_dict["__typename"])
    if not event_type:
        raise Exception("unhandled event type %s" % event_dict["__typename"])

    # Get event_specific_data
    event_specific_data = None
    if event_type == DagsterEventType.STEP_OUTPUT:
        event_specific_data = StepOutputData(
            step_output_handle=StepOutputHandle(event_dict["stepKey"], event_dict["outputName"]),
            type_check_data=TypeCheckData(
                success=event_dict["typeCheck"]["success"],
                label=event_dict["typeCheck"]["label"],
                description=event_dict.get("description"),
                metadata_entries=list(
                    event_metadata_entries(event_dict.get("metadataEntries")) or []
                ),
            ),
        )

    elif event_type == DagsterEventType.STEP_INPUT:
        event_specific_data = StepInputData(
            input_name=event_dict["inputName"],
            type_check_data=TypeCheckData(
                success=event_dict["typeCheck"]["success"],
                label=event_dict["typeCheck"]["label"],
                description=event_dict.get("description"),
                metadata_entries=list(
                    event_metadata_entries(event_dict.get("metadataEntries")) or []
                ),
            ),
        )
    elif event_type == DagsterEventType.STEP_SUCCESS:
        event_specific_data = StepSuccessData(0.0)

    elif event_type == DagsterEventType.STEP_UP_FOR_RETRY:
        event_specific_data = StepRetryData(
            error=error_from_data(event_dict["retryError"]),
            seconds_to_wait=event_dict["secondsToWait"],
        )

    elif event_type == DagsterEventType.STEP_MATERIALIZATION:
        materialization = event_dict["materialization"]
        event_specific_data = StepMaterializationData(
            materialization=materialization_from_data(materialization)
        )
    elif event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        expectation_result = expectation_result_from_data(event_dict["expectationResult"])
        event_specific_data = StepExpectationResultData(expectation_result)

    elif event_type == DagsterEventType.STEP_FAILURE:
        event_specific_data = StepFailureData(
            error_from_data(event_dict["error"]),
            UserFailureData(
                label=event_dict["failureMetadata"]["label"],
                description=event_dict["failureMetadata"]["description"],
                metadata_entries=list(
                    event_metadata_entries(event_dict.get("metadataEntries")) or []
                ),
            )
            if event_dict.get("failureMetadata")
            else None,
        )

    elif event_type == DagsterEventType.ENGINE_EVENT:
        event_specific_data = EngineEventData(
            metadata_entries=list(event_metadata_entries(event_dict.get("metadataEntries"))),
            marker_start=event_dict.get("markerStart"),
            marker_end=event_dict.get("markerEnd"),
            error=error_from_data(event_dict["engineError"])
            if event_dict.get("engineError")
            else None,
        )

    return DagsterEvent(
        event_type_value=event_type.value,
        pipeline_name=pipeline_name,
        step_key=event_dict.get("stepKey"),
        solid_handle=SolidHandle.from_string(event_dict["solidHandleID"])
        if event_dict.get("solidHandleID")
        else None,
        # at the time of writing this:
        # * 'COMPUTE` is the only step kind
        # * this code should get deleted in the near future as we move away from
        #   dagster-graphql CLI as what we invoke in dask/k8s/etc.
        step_kind_value="COMPUTE" if event_dict.get("stepKey") else None,
        logging_tags=None,
        event_specific_data=event_specific_data,
    )


def construct_execute_plan_variables(
    recon_repo, mode, run_config, pipeline_name, run_id, step_keys
):
    check.inst_param(recon_repo, "recon_repo", ReconstructableRepository)
    check.str_param(mode, "mode")
    check.dict_param(run_config, "run_config")
    check.str_param(pipeline_name, "pipeline_name")
    check.str_param(run_id, "run_id")
    check.list_param(step_keys, "step_keys", of_type=str)

    variables = {
        "executionParams": {
            "runConfigData": run_config,
            "mode": mode,
            "selector": {
                "repositoryLocationName": "<<in_process>>",
                "repositoryName": recon_repo.get_definition().name,
                "pipelineName": pipeline_name,
            },
            "executionMetadata": {"runId": run_id},
            "stepKeys": step_keys,
        },
    }

    return variables


def parse_raw_log_lines(log_lines):
    """Parses the raw log lines response from a dagster-graphql CLI invocation, typically from a
    Docker or Kubernetes container.

     - Log lines don't necessarily come back in order
     - Something else might log JSON
     - Docker appears to silently split very long log lines -- this is undocumented behavior

    Args:
        log_lines (List[str]): Log lines containing response JSON

    Returns:
        Dict: Parsed JSON response
    """
    res = None
    lines = []
    coalesced = []
    in_split_line = False
    for line in log_lines:
        if not in_split_line and line.startswith("{"):
            if line.endswith("}"):
                lines.append(line)
                continue
            else:
                coalesced.append(line)
                in_split_line = True
                continue
        if in_split_line:
            coalesced.append(line)
            if line.endswith("}"):
                lines.append("".join(coalesced))
                coalesced = []
                in_split_line = False

    for line in reversed(lines):
        try:
            res = seven.json.loads(line)
            break
        # If we don't get a GraphQL response, check the next line
        except seven.JSONDecodeError:
            continue

    return res
