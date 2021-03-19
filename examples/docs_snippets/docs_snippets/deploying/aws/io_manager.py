from dagster import ModeDefinition
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

prod_mode = ModeDefinition(
    name="prod",
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
)
