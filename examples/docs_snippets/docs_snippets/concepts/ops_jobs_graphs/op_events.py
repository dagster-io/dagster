# ruff: isort: skip_file

import dagster as dg


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
import dagster as dg


@dg.op
def my_metadata_output(context: dg.OpExecutionContext) -> dg.Output:
    df = get_some_data()
    return dg.Output(
        df,
        metadata={
            "text_metadata": "Text-based metadata for this event",
            "dashboard_url": dg.MetadataValue.url(
                "http://mycoolsite.com/url_for_my_data"
            ),
            "raw_count": len(df),
            "size (bytes)": calculate_bytes(df),
        },
    )


# end_op_output_3

# start_op_output_4
import dagster as dg


# Using dg.Output as type annotation without inner type
@dg.op
def my_output_op() -> dg.Output:
    return dg.Output("some_value", metadata={"some_metadata": "a_value"})


# A single output with a parameterized type annotation
@dg.op
def my_output_generic_op() -> dg.Output[int]:
    return dg.Output(5, metadata={"some_metadata": "a_value"})


# Multiple outputs using parameterized type annotation
@dg.op(out={"int_out": dg.Out(), "str_out": dg.Out()})
def my_multiple_generic_output_op() -> tuple[dg.Output[int], dg.Output[str]]:
    return (
        dg.Output(5, metadata={"some_metadata": "a_value"}),
        dg.Output("foo", metadata={"some_metadata": "another_value"}),
    )


# end_op_output_4

# start_metadata_expectation_op
import dagster as dg


@dg.op
def my_metadata_expectation_op(context: dg.OpExecutionContext, df):
    df = do_some_transform(df)
    context.log_event(
        dg.ExpectationResult(
            success=len(df) > 0,
            description="ensure dataframe has rows",
            metadata={
                "text_metadata": "Text-based metadata for this event",
                "dashboard_url": dg.MetadataValue.url(
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
import dagster as dg


@dg.op
def my_failure_op():
    path = "/path/to/files"
    my_files = get_files(path)
    if len(my_files) == 0:
        raise dg.Failure(
            description="No files to process",
            metadata={
                "filepath": dg.MetadataValue.path(path),
                "dashboard_url": dg.MetadataValue.url("http://mycoolsite.com/failures"),
            },
        )
    return some_calculation(my_files)


# end_failure_op

# start_retry_op
import dagster as dg


@dg.op
def my_retry_op():
    try:
        result = flaky_operation()
    except Exception as e:
        raise dg.RetryRequested(max_retries=3) from e
    return result


# end_retry_op

# start_asset_op
import dagster as dg


@dg.op
def my_asset_op(context: dg.OpExecutionContext):
    df = get_some_data()
    store_to_s3(df)
    context.log_event(
        dg.AssetMaterialization(
            asset_key="s3.my_asset",
            description="A df I stored in s3",
        )
    )

    result = do_some_transform(df)
    return result


# end_asset_op

# start_asset_op_yield
import dagster as dg


@dg.op
def my_asset_op_yields():
    df = get_some_data()
    store_to_s3(df)
    yield dg.AssetMaterialization(
        asset_key="s3.my_asset",
        description="A df I stored in s3",
    )

    result = do_some_transform(df)
    yield dg.Output(result)


# end_asset_op_yield

# start_expectation_op
import dagster as dg


@dg.op
def my_expectation_op(context: dg.OpExecutionContext, df):
    do_some_transform(df)
    context.log_event(
        dg.ExpectationResult(
            success=len(df) > 0, description="ensure dataframe has rows"
        )
    )
    return df


# end_expectation_op

# start_yield_outputs
import dagster as dg


@dg.op(out={"out1": dg.Out(str), "out2": dg.Out(int)})
def my_op_yields():
    yield dg.Output(5, output_name="out2")
    yield dg.Output("foo", output_name="out1")


# end_yield_outputs
