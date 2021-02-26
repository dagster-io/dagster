# pylint: disable=unused-argument

from dagster import EventMetadataEntry, ExpectationResult, Output, solid


def do_some_transform(df):
    return df


def calculate_bytes(df):
    return 1.0


# start_expectation_solids_marker_0
@solid
def my_simple_solid(context, df):
    do_some_transform(df)
    return df


# end_expectation_solids_marker_0

# start_expectation_solids_marker_1
@solid
def my_expectation_solid(context, df):
    do_some_transform(df)
    yield ExpectationResult(success=len(df) > 0, description="ensure dataframe has rows")
    yield Output(df)


# end_expectation_solids_marker_1

# start_metadata
@solid
def my_metadata_expectation_solid(context, df):
    do_some_transform(df)
    yield ExpectationResult(
        success=len(df) > 0,
        description="ensure dataframe has rows",
        metadata_entries=[
            EventMetadataEntry.text("Text-based metadata for this event", label="text_metadata"),
            EventMetadataEntry.url("http://mycoolsite.com/url_for_my_data", label="dashboard_url"),
            EventMetadataEntry.float(1.0 * len(df), "row count"),
            EventMetadataEntry.float(calculate_bytes(df), "size (bytes)"),
        ],
    )
    yield Output(df)


# end_metadata
