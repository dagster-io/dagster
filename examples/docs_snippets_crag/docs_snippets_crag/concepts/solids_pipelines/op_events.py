# pylint: disable=unused-argument
from dagster import (
    AssetMaterialization,
    EventMetadata,
    ExpectationResult,
    Failure,
    Output,
    OutputDefinition,
    RetryRequested,
)


def do_some_transform(_):
    return []


def calculate_bytes(_):
    return 0.0


def get_some_data():
    return []


def some_calculation(_):
    return 0


def get_files(_path):
    return []


def store_to_s3(_):
    return


def flaky_operation():
    return 0


# start_op_output_0


@op
def my_simple_yield_op(context):
    yield Output(1)


# end_op_output_0

# start_op_output_1


@op
def my_simple_return_op(context):
    return 1


# end_op_output_1

# start_op_output_2


@op(
    output_defs=[
        OutputDefinition(name="my_output"),
    ]
)
def my_named_yield_op(context):
    yield Output(1, output_name="my_output")


# end_op_output_2

# start_op_output_3


@op
def my_metadata_output(context):
    df = get_some_data()
    yield Output(
        df,
        metadata={
            "text_metadata": "Text-based metadata for this event",
            "dashboard_url": EventMetadata.url("http://mycoolsite.com/url_for_my_data"),
            "raw_count": len(df),
            "size (bytes)": calculate_bytes(df),
        },
    )


# end_op_output_3

# start_metadata_expectation_op


@op
def my_metadata_expectation_op(context, df):
    df = do_some_transform(df)
    yield ExpectationResult(
        success=len(df) > 0,
        description="ensure dataframe has rows",
        metadata={
            "text_metadata": "Text-based metadata for this event",
            "dashboard_url": EventMetadata.url("http://mycoolsite.com/url_for_my_data"),
            "raw_count": len(df),
            "size (bytes)": calculate_bytes(df),
        },
    )
    yield Output(df)


# end_metadata_expectation_op

# start_failure_op


@op
def my_failure_op():
    path = "/path/to/files"
    my_files = get_files(path)
    if len(my_files) == 0:
        raise Failure(
            description="No files to process",
            metadata={
                "filepath": EventMetadata.path(path),
                "dashboard_url": EventMetadata.url("http://mycoolsite.com/failures"),
            },
        )
    return some_calculation(my_files)


# end_failure_op

# start_failure_metadata_op


@op
def my_failure_metadata_op():
    path = "/path/to/files"
    my_files = get_files(path)
    if len(my_files) == 0:
        raise Failure(
            description="No files to process",
            metadata={
                "filepath": EventMetadata.path(path),
                "dashboard_url": EventMetadata.url("http://mycoolsite.com/failures"),
            },
        )
    return some_calculation(my_files)


# end_failure_metadata_op

# start_retry_op


@op
def my_retry_op():
    try:
        result = flaky_operation()
    except:
        raise RetryRequested(max_retries=3)
    return result


# end_retry_op

# start_asset_op


@op
def my_asset_op(context):
    df = get_some_data()
    store_to_s3(df)
    yield AssetMaterialization(
        asset_key="s3.my_asset",
        description="A df I stored in s3",
    )

    result = do_some_transform(df)
    yield Output(result)


# end_asset_op
