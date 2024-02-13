from dagster import configured, resource

# start_op_marker


@resource(config_schema={"region": str, "use_unsigned_session": bool})
def s3_session(_init_context):
    """Connect to S3."""


# end_op_marker

# start_configured_marker

east_unsigned_s3_session = s3_session.configured(
    {"region": "us-east-1", "use_unsigned_session": False}
)
# end_configured_marker


# start_configured_decorator_marker
@configured(s3_session)
def west_unsigned_s3_session(_init_context):
    return {"region": "us-west-1", "use_unsigned_session": False}


# end_configured_decorator_marker


# start_configured_method_marker
west_signed_s3_session = configured(s3_session)(
    {"region": "us-west-1", "use_unsigned_session": False}
)


# end_configured_method_marker
