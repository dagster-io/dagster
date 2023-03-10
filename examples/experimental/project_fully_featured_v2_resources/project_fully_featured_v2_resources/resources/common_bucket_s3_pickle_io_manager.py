from typing import Any

from dagster import build_init_resource_context
from dagster._config.structured_config import ConfigurableIOManagerFactory, ResourceDependency
from dagster._core.storage.io_manager import IOManager
from dagster_aws.s3 import s3_pickle_io_manager


class CommonBucketS3PickleIOManager(ConfigurableIOManagerFactory):
    """A version of the s3_pickle_io_manager that gets its bucket from another resource."""

    s3_bucket: str
    s3: ResourceDependency[Any]

    def create_io_manager(self, context) -> IOManager:
        return s3_pickle_io_manager(
            build_init_resource_context(
                config={"s3_bucket": self.s3_bucket},
                resources={"s3": self.s3},
            )
        )
