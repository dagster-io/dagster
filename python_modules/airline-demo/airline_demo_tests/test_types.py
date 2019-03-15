import sys
import tempfile

from airline_demo.resources import spark_session_local, tempfile_resource
from airline_demo.types import SparkDataFrameSerializationStrategy


class MockResources(object):
    def __init__(self, spark, tempfile_):
        self.spark = spark
        self.tempfile = tempfile_


class MockPipelineContext(object):
    def __init__(self, spark, tempfile_):
        self.resources = MockResources(spark, tempfile_)


def test_spark_data_frame_serialization():
    spark = spark_session_local.resource_fn(None)
    if sys.version_info > (3,):
        tempfile_ = tempfile_resource.resource_fn(None).__next__()
    else:
        tempfile_ = tempfile_resource.resource_fn(None).next()

    try:
        serialization_strategy = SparkDataFrameSerializationStrategy()

        pipeline_context = MockPipelineContext(spark, tempfile_)

        df = spark.createDataFrame([('Foo', 1), ('Bar', 2)])

        with tempfile.NamedTemporaryFile(delete=False) as tempfile_obj:
            serialization_strategy.serialize_value(pipeline_context, df, tempfile_obj)

            tempfile_obj.close()

        with open(tempfile_obj.name, 'r+b') as tempfile_obj:
            new_df = serialization_strategy.deserialize_value(pipeline_context, tempfile_obj)

        assert set(map(lambda x: x[0], new_df.collect())) == set(['Bar', 'Foo'])
        assert set(map(lambda x: x[1], new_df.collect())) == set([1, 2])
    finally:
        tempfile_.close()
