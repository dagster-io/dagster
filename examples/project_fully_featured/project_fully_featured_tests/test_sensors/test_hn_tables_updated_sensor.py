import json
from typing import List, Tuple
from unittest import mock
from numpy import partition
import pandas as pd
import pyspark as spark
from pyspark.sql import (
    SparkSession,
    Row,
)
from dagster._core.storage.io_manager import io_manager
from pyspark.sql.types import IntegerType, StringType, StructField, StructType
from project_fully_featured.sensors.hn_tables_updated_sensor import (
    make_hn_tables_updated_sensor,
)
from project_fully_featured.repository import hacker_news_repository

from dagster import (
    EventLogRecord,
    GraphDefinition,
    build_sensor_context,
    materialize,
    build_multi_asset_sensor_context,
    AssetKey,
    SourceAsset,
    AssetSelection,
    IOManager,
)
from dagster._core.test_utils import instance_for_test
from project_fully_featured.assets.core.items import comments, stories, items, hourly_partitions


def get_sensor_context(instance):
    return build_multi_asset_sensor_context(
        asset_keys=[
            AssetKey(["snowflake", "core", "comments"]),
            AssetKey(["snowflake", "core", "stories"]),
        ],
        instance=instance,
        repository_def=hacker_news_repository,
        set_cursor_to_latest_materializations=True,
    )


class MockIOManager(IOManager):
    def load_input(self, context):
        schema = StructType([StructField("type", StringType())])
        rows = [Row(name="comment"), Row(name="story")]
        spark = SparkSession.builder.getOrCreate()
        return spark.createDataFrame(rows, schema)

    def handle_output(self, context, obj) -> None:
        pass


@io_manager
def mock_io_manager():
    return MockIOManager()


def materialize_comments_or_stories(assets, instance):
    items_source_asset = SourceAsset(
        key="items", io_manager_key="warehouse_io_manager", partitions_def=hourly_partitions
    )
    assert materialize(
        [*assets, items_source_asset],
        resources={"warehouse_io_manager": mock_io_manager},
        instance=instance,
        partition_key="2021-01-01-00:00",
    ).success


def test_first_events():
    with instance_for_test() as instance:
        context = get_sensor_context(instance)
        materialize_comments_or_stories([comments, stories], instance)

        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 1


def test_nothing_new():
    with instance_for_test() as instance:
        # Cursor points to latest materialization
        materialize_comments_or_stories([comments, stories], instance)
        context = get_sensor_context(instance)

        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 0


def test_new_comments_old_stories():
    with instance_for_test() as instance:
        materialize_comments_or_stories([comments, stories], instance)
        context = get_sensor_context(instance)

        # New materialization for comments after cursor
        # Cursor points to latest materialization for stories
        materialize_comments_or_stories([comments], instance)
        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 0


def test_old_comments_new_stories():
    with instance_for_test() as instance:
        materialize_comments_or_stories([comments, stories], instance)
        context = get_sensor_context(instance)

        # New materialization for stories after cursor
        # Cursor points to latest materialization for comments
        materialize_comments_or_stories([stories], instance)
        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 0


def test_both_new():
    with instance_for_test() as instance:
        materialize_comments_or_stories([comments, stories], instance)
        context = get_sensor_context(instance)

        materialize_comments_or_stories([comments, stories], instance)
        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 1
