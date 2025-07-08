# ruff: isort: skip_file

from dagster import job, op, OpExecutionContext


def read_df():
    return range(372)


def read_df_for_date(_):
    return 1


def persist_to_storage(_):
    return "tmp"


def calculate_bytes(_):
    return 1.0


# start_observation_asset_marker_0
import dagster as dg


@dg.op
def observation_op(context: dg.OpExecutionContext):
    df = read_df()
    context.log_event(
        dg.AssetObservation(
            asset_key="observation_asset", metadata={"num_rows": len(df)}
        )
    )
    return 5


# end_observation_asset_marker_0

# start_partitioned_asset_observation
import dagster as dg


class MyOpConfig(dg.Config):
    date: str


@dg.op
def partitioned_dataset_op(context: dg.OpExecutionContext, config: MyOpConfig):
    partition_date = config.date
    df = read_df_for_date(partition_date)
    context.log_event(
        dg.AssetObservation(
            asset_key="my_partitioned_dataset", partition=partition_date
        )
    )
    return df


# end_partitioned_asset_observation


# start_observation_asset_marker_2
import dagster as dg


@dg.op
def observes_dataset_op(context: dg.OpExecutionContext):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    context.log_event(
        dg.AssetObservation(
            asset_key="my_dataset",
            metadata={
                "text_metadata": "Text-based metadata for this event",
                "path": dg.MetadataValue.path(remote_storage_path),
                "dashboard_url": dg.MetadataValue.url(
                    "http://mycoolsite.com/url_for_my_data"
                ),
                "size (bytes)": calculate_bytes(df),
            },
        )
    )
    return remote_storage_path


# end_observation_asset_marker_2


@dg.job
def my_observation_job():
    observation_op()


@dg.job
def my_dataset_job():
    observes_dataset_op()
