from collections import defaultdict

from dagster.core.definitions.events import ObjectStoreOperationType
from dagster.core.execution.plan.objects import StepOutputHandle


def get_addresses_for_step_output_versions_helper(
    step_output_versions, object_store_operation_records
):
    """
    Args:
        step_output_versions (Dict[(str, StepOutputHandle), str]):
            (pipeline name, step output handle) -> version.
        object_store_operation_records (List[Tuple[float, DagsterEvent]]):
            Logged step output records.

    Returns:
        Dict[(str, StepOutputHandle), str]: (pipeline name, step output handle) -> address.
            For each step output, an address if there is one and None otherwise.
    """
    # if multiple output events wrote to the same address, only the latest one is relevant
    latest_version_by_address = {}
    latest_timestamp_by_address = defaultdict(int)
    for timestamp, dagster_event in object_store_operation_records:
        output_storage_data = dagster_event.event_specific_data
        address = output_storage_data.address
        version = output_storage_data.version
        pipeline_name = dagster_event.pipeline_name
        step_output_handle = StepOutputHandle(
            dagster_event.step_key, output_storage_data.value_name
        )

        if (
            output_storage_data.op == ObjectStoreOperationType.SET_OBJECT.value
            and address
            and latest_timestamp_by_address[address] < timestamp
        ):
            latest_timestamp_by_address[address] = timestamp
            latest_version_by_address[address] = (
                pipeline_name,
                step_output_handle,
                version,
            )

    # finally, we select the addresses that correspond to the steps we're concerned with.
    # ideally, we'd be pushing down this filter to the initial query so that we don't need to pull
    # every single step output event across all runs for all pipelines. to do that, we'll need to
    # add columns to the event schema.
    step_output_versions_set = set(step_output_versions.items())

    address_by_output = {
        (pipeline_name, step_output_handle): address
        for address, (
            pipeline_name,
            step_output_handle,
            version,
        ) in latest_version_by_address.items()
        if ((pipeline_name, step_output_handle), version) in step_output_versions_set
    }

    return address_by_output
