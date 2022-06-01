# isort: skip_file
# pylint: disable=unused-argument,reimported
from dagster import (
    AssetMaterialization,
    ExpectationResult,
    Failure,
    MetadataValue,
    Out,
    Output,
    RetryRequested,
    op,
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


# start_op_output_3
from dagster import MetadataValue, Output, op


@op
def my_metadata_output(context) -> Output:
    df = get_some_data()
    return Output(
        df,
        metadata={
            "text_metadata": "Text-based metadata for this event",
            "dashboard_url": MetadataValue.url("http://mycoolsite.com/url_for_my_data"),
            "raw_count": len(df),
            "size (bytes)": calculate_bytes(df),
        },
    )


# end_op_output_3

# start_op_output_4
from dagster import Output, op
from typing import Tuple

# Using Output as type annotation without inner type
@op
def my_output_op() -> Output:
    return Output("some_value")


# A single output with a parameterized type annotation
@op
def my_output_generic_op() -> Output[int]:
    return Output(5)


# Multiple outputs using parameterized type annotation
@op(out={"int_out": Out(), "str_out": Out()})
def my_multiple_generic_output_op() -> Tuple[Output[int], Output[str]]:
    return (Output(5), Output("foo"))


# end_op_output_4

# start_metadata_expectation_op
from dagster import ExpectationResult, MetadataValue, op


@op
def my_metadata_expectation_op(context, df):
    df = do_some_transform(df)
    context.log_event(
        ExpectationResult(
            success=len(df) > 0,
            description="ensure dataframe has rows",
            metadata={
                "text_metadata": "Text-based metadata for this event",
                "dashboard_url": MetadataValue.url(
                    "http://mycoolsite.com/url_for_my_data"
                ),
                "raw_count": len(df),
                "size (bytes)": calculate_bytes(df),
            },
        )
    )
    return df


# end_metadata_expectation_op

# start_failure_op
from dagster import Failure, op


@op
def my_failure_op():
    path = "/path/to/files"
    my_files = get_files(path)
    if len(my_files) == 0:
        raise Failure(
            description="No files to process",
            metadata={
                "filepath": MetadataValue.path(path),
                "dashboard_url": MetadataValue.url("http://mycoolsite.com/failures"),
            },
        )
    return some_calculation(my_files)


# end_failure_op

# start_failure_metadata_op
from dagster import Failure, op


@op
def my_failure_metadata_op():
    path = "/path/to/files"
    my_files = get_files(path)
    if len(my_files) == 0:
        raise Failure(
            description="No files to process",
            metadata={
                "filepath": MetadataValue.path(path),
                "dashboard_url": MetadataValue.url("http://mycoolsite.com/failures"),
            },
        )
    return some_calculation(my_files)


# end_failure_metadata_op

# start_retry_op
from dagster import RetryRequested, op


@op
def my_retry_op():
    try:
        result = flaky_operation()
    except Exception as e:
        raise RetryRequested(max_retries=3) from e
    return result


# end_retry_op

# start_asset_op
from dagster import AssetMaterialization, op


@op
def my_asset_op(context):
    df = get_some_data()
    store_to_s3(df)
    context.log_event(
        AssetMaterialization(
            asset_key="s3.my_asset",
            description="A df I stored in s3",
        )
    )

    result = do_some_transform(df)
    return result


# end_asset_op

# start_asset_op_yield
from dagster import AssetMaterialization, Output, op


@op
def my_asset_op_yields():
    df = get_some_data()
    store_to_s3(df)
    yield AssetMaterialization(
        asset_key="s3.my_asset",
        description="A df I stored in s3",
    )

    result = do_some_transform(df)
    yield Output(result)


# end_asset_op_yield

# start_expectation_op
from dagster import ExpectationResult, op


@op
def my_expectation_op(context, df):
    do_some_transform(df)
    context.log_event(
        ExpectationResult(success=len(df) > 0, description="ensure dataframe has rows")
    )
    return df


# end_expectation_op

# start_yield_outputs
from dagster import Output, op


@op(out={"out1": Out(str), "out2": Out(int)})
def my_op_yields():
    yield Output(5, output_name="out2")
    yield Output("foo", output_name="out1")


# end_yield_outputs
