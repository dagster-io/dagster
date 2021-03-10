# pylint: disable=unused-argument
from dagster import solid, ExpectationResult, EventMetadataEntry, Output


def do_some_transform(_):
    return []


def calculate_bytes(_):
    return 0


# start_solid_output_0


@solid
def my_yield_solid(context):
    yield Output(1)


# end_solid_output_0

# start_solid_output_1


@solid
def return_solid(context):
    return 1


# end_solid_output_1

# start_solid_output_2


@solid
def yield_solid(context):
    yield Output(1, "result")


# end_solid_output_2

# start_metadata_expectation_solid


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


# end_metadata_expectation_solid