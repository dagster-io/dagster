from collections import defaultdict


def get_addresses_for_step_output_versions_helper(step_output_versions, step_output_records):
    """
    Args:
        step_output_versions (Dict[(str, StepOutputHandle), str]):
            (pipeline name, step output handle) -> version.
        step_output_records (List[Tuple[float, DagsterEvent]]):
            Logged step output records.

    Returns:
        Dict[(str, StepOutputHandle), str]: (pipeline name, step output handle) -> address.
            For each step output, an address if there is one and None otherwise.
    """
    # if multiple output events wrote to the same address, only the latest one is relevant
    latest_version_by_address = {}
    latest_timestamp_by_address = defaultdict(int)
    for timestamp, dagster_event in step_output_records:
        step_output_data = dagster_event.event_specific_data
        address = step_output_data.address
        version = step_output_data.version
        pipeline_name = dagster_event.pipeline_name
        step_output = step_output_data.step_output_handle

        if address and latest_timestamp_by_address[address] < timestamp:
            latest_timestamp_by_address[address] = timestamp
            latest_version_by_address[address] = (
                pipeline_name,
                step_output,
                version,
            )

    # finally, we select the addresses that correspond to the steps we're concerned with.
    # ideally, we'd be pushing down this filter to the initial query so that we don't need to pull
    # every single step output event across all runs for all pipelines. to do that, we'll need to
    # add columns to the event schema.
    step_output_versions_set = set(step_output_versions.items())
    address_by_output = {
        (pipeline_name, step_output): address
        for address, (pipeline_name, step_output, version) in latest_version_by_address.items()
        if ((pipeline_name, step_output), version) in step_output_versions_set
    }

    return address_by_output
