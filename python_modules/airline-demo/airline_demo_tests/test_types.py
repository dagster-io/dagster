import os
import shutil
import uuid

from dagster.core.object_store import FileSystemObjectStore, get_valid_target_path

from airline_demo.resources import spark_session_local
from airline_demo.types import SparkDataFrameType


class MockResources(object):
    def __init__(self, spark):
        self.spark = spark


class MockPipelineContext(object):
    def __init__(self, spark):
        self.resources = MockResources(spark)


def test_spark_data_frame_serialization_file_systemn():
    run_id = str(uuid.uuid4())

    def set_object(self, obj, _context, _runtime_type, paths):
        target_path = get_valid_target_path(self.root, paths)
        obj.write.parquet('file://' + target_path)
        return target_path

    def get_object(self, context, _runtime_type, paths):
        return context.resources.spark.read.parquet(get_valid_target_path(self.root, paths))

    object_store = FileSystemObjectStore(
        run_id=run_id,
        types_to_register={
            SparkDataFrameType: {'get_object': get_object, 'set_object': set_object}
        },
    )

    spark = spark_session_local.resource_fn(None)
    pipeline_context = MockPipelineContext(spark)

    df = spark.createDataFrame([('Foo', 1), ('Bar', 2)])

    try:
        object_store.set_value(df, pipeline_context, SparkDataFrameType, ['df'])

        assert os.path.isdir(os.path.join(object_store.root, 'df'))
        assert os.path.isfile(os.path.join(object_store.root, 'df', '_SUCCESS'))

        new_df = object_store.get_value(pipeline_context, SparkDataFrameType, ['df'])

        assert set(map(lambda x: x[0], new_df.collect())) == set(['Bar', 'Foo'])
        assert set(map(lambda x: x[1], new_df.collect())) == set([1, 2])
    finally:
        shutil.rmtree(object_store.root)
