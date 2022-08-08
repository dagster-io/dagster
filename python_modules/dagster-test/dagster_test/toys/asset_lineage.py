import datetime
import os
import random
import string

import pandas as pd

from dagster import (
    Out,
    op,
    Array,
    AssetKey,
    Field,
    MetadataEntry,
    MetadataValue,
    Output,
    Partition,
)
from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager
from dagster._core.storage.io_manager import io_manager
from dagster._legacy import (
    ModeDefinition,
    OutputDefinition,
    PartitionSetDefinition,
    pipeline,
    solid,
)


def get_date_partitions():
    """Every day in 2020"""
    d1 = datetime.date(2020, 1, 1)
    d2 = datetime.date(2021, 1, 1)
    days = [d1 + datetime.timedelta(days=x) for x in range((d2 - d1).days + 1)]

    return [Partition(day.strftime("%Y-%m-%d")) for day in days]


def run_config_for_date_partition(partition):
    date = partition.value

    return {
        "solids": {
            "download_data": {"outputs": {"result": {"partitions": [date]}}},
            "split_action_types": {
                "outputs": {
                    "comments": {"partitions": [date]},
                    "reviews": {"partitions": [date]},
                }
            },
            "top_10_comments": {"outputs": {"result": {"partitions": [date]}}},
            "top_10_reviews": {"outputs": {"result": {"partitions": [date]}}},
            "daily_top_action": {"outputs": {"result": {"partitions": [date]}}},
        }
    }


asset_lineage_partition_set = PartitionSetDefinition(
    name="date_partition_set",
    pipeline_name="asset_lineage_pipeline",
    partition_fn=get_date_partitions,
    run_config_fn_for_partition=run_config_for_date_partition,
)


def metadata_for_actions(df):
    return {
        "min_score": int(df["score"].min()),
        "max_score": int(df["score"].max()),
        "sample rows": MetadataValue.md(df[:5].to_markdown()),
    }


class MyDatabaseIOManager(PickledObjectFilesystemIOManager):
    def _get_path(self, context):
        keys = context.get_identifier()

        return os.path.join("/tmp", *keys)

    def handle_output(self, context, obj):
        super().handle_output(context, obj)
        # can pretend this actually came from a library call
        yield MetadataEntry(
            label="num rows written to db",
            description=None,
            entry_data=MetadataValue.int(len(obj)),
        )

    def get_output_asset_key(self, context):
        return AssetKey(
            [
                "my_database",
                context.metadata["table_name"],
            ]
        )

    def get_output_asset_partitions(self, context):
        return set(context.config.get("partitions", []))


@io_manager(output_config_schema={"partitions": Field(Array(str), is_required=False)})
def my_db_io_manager(_):
    return MyDatabaseIOManager()


@op(
    out={
        {"table_name": "raw_actions"}: Out(
            io_manager_key="my_db_io_manager",
        )
    },
)
def download_data(_):
    n_entries = random.randint(100, 1000)

    def user_id():
        return "".join(random.choices(string.ascii_uppercase, k=10))

    # generate some random data
    data = {
        "user_id": [user_id() for i in range(n_entries)],
        "action_type": [
            random.choices(["story", "comment"], [0.15, 0.85])[0]
            for i in range(n_entries)
        ],
        "score": [random.randint(0, 10000) for i in range(n_entries)],
    }
    df = pd.DataFrame.from_dict(data)
    yield Output(df, metadata=metadata_for_actions(df))


@op(
    out={
        "reviews": Out(
            io_manager_key="my_db_io_manager",
            metadata={"table_name": "reviews"},
        ),
        "comments": Out(
            io_manager_key="my_db_io_manager",
            metadata={"table_name": "comments"},
        ),
    }
)
def split_action_types(_, df):

    reviews_df = df[df["action_type"] == "story"]
    comments_df = df[df["action_type"] == "comment"]
    yield Output(
        reviews_df,
        "reviews",
        metadata=metadata_for_actions(reviews_df),
    )
    yield Output(comments_df, "comments", metadata=metadata_for_actions(comments_df))


def best_n_actions(n, action_type):
    @op(
        name=f"top_{n}_{action_type}",
        out={
            {"table_name": f"best_{action_type}"}: Out(
                io_manager_key="my_db_io_manager",
            )
        },
    )
    def _best_n_actions(_, df):
        df = df.nlargest(n, "score")
        return Output(
            df,
            metadata={"data": MetadataValue.md(df.to_markdown())},
        )

    return _best_n_actions


top_10_reviews = best_n_actions(10, "reviews")
top_10_comments = best_n_actions(10, "comments")


@op(
    out={
        {"table_name": "daily_best_action"}: Out(
            io_manager_key="my_db_io_manager",
        )
    }
)
def daily_top_action(_, df1, df2):
    df = pd.concat([df1, df2]).nlargest(1, "score")
    return Output(df, metadata={"data": MetadataValue.md(df.to_markdown())})


@pipeline(
    mode_defs=[ModeDefinition(resource_defs={"my_db_io_manager": my_db_io_manager})]
)
def asset_lineage_pipeline():
    reviews, comments = split_action_types(download_data())
    daily_top_action(top_10_reviews(reviews), top_10_comments(comments))
