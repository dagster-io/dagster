from dagster import ExecuteInProcessResult


def get_saved_path(result: ExecuteInProcessResult, asset_name: str) -> str:
    path = (
        list(filter(lambda evt: evt.is_handled_output, result.events_for_node(asset_name)))[0]  # noqa: RUF015
        .event_specific_data.metadata["path"]  # type: ignore
        .value
    )
    assert isinstance(path, str)
    return path


DEPRECATED_STORAGE_METADATA_STRING = "dagster-polars storage metadata"
