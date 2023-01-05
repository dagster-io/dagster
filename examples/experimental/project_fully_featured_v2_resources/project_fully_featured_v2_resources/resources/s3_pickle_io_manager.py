from dagster import IOManagerDefinition
from dagster._config.structured_config import StructuredIOManagerAdapter
from dagster_aws.s3.io_manager import s3_pickle_io_manager


class S3PickledIOManagerAdapter(StructuredIOManagerAdapter):
    s3_bucket: str

    def wrapped_io_manager(self) -> IOManagerDefinition:
        return s3_pickle_io_manager
