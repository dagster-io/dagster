from dagster import resource


@resource(config_schema={"region": str, "use_unsigned_session": bool})
def s3_session(_init_context):
    """Connect to S3"""


east_unsigned_s3_session = s3_session.configured(
    {"region": "us-east-1", "use_unsigned_session": False}
)
