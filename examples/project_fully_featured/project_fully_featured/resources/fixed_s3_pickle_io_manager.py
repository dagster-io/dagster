import pickle

import boto3

from dagster import IOManager, MetadataEntry, io_manager


def s3_client():
    return boto3.resource("s3", use_ssl=True).meta.client


class FixedS3PickleIOManager(IOManager):
    def load_input(self, context):
        key = context.asset_key.path[-1]
        bucket = context.resource_config["bucket"]
        return pickle.loads(s3_client().get_object(Bucket=bucket, Key=key)["Body"].read())

    def handle_output(self, context, obj):
        key = context.asset_key.path[-1]
        bucket = context.resource_config["bucket"]

        context.log.debug("about to pickle object")
        pickled_obj = pickle.dumps(obj)
        yield MetadataEntry.int(len(pickled_obj), "Bytes")
        client = s3_client()
        context.log.debug("created S3 client")
        client.put_object(Bucket=bucket, Key=key, Body=pickled_obj)


@io_manager(config_schema={"bucket": str})
def fixed_s3_pickle_io_manager(_) -> FixedS3PickleIOManager:
    return FixedS3PickleIOManager()
