from dagster import Field, StringSource, resource
from dagster.utils.merger import merge_dicts

from .file_manager import S3FileManager
from .utils import construct_s3_client

S3_SESSION_CONFIG = {
    "use_unsigned_session": Field(
        bool,
        description="Specifies whether to use an unsigned S3 session",
        is_required=False,
        default_value=False,
    ),
    "region_name": Field(
        str, description="Specifies a custom region for the S3 session", is_required=False
    ),
    "endpoint_url": Field(
        StringSource,
        description="Specifies a custom endpoint for the S3 session",
        is_required=False,
    ),
    "max_attempts": Field(
        int,
        description="This provides Boto3's retry handler with a value of maximum retry attempts, "
        "where the initial call counts toward the max_attempts value that you provide",
        is_required=False,
        default_value=5,
    ),
    "profile_name": Field(
        str,
        description="Specifies a profile to connect that session",
        is_required=False,
    ),
}


@resource(S3_SESSION_CONFIG)
def s3_resource(context):
    """Resource that gives access to S3.

    The underlying S3 session is created by calling
    :py:func:`boto3.session.Session(profile_name) <boto3:boto3.session>`.
    The returned resource object is an S3 client, an instance of `botocore.client.S3`.

    Example:

        .. code-block:: python

            from dagster import build_op_context, job, op
            from dagster_aws.s3 import s3_resource

            @op(required_resource_keys={'s3'})
            def example_s3_op(context):
                return context.resources.s3.list_objects_v2(
                    Bucket='my-bucket',
                    Prefix='some-key'
                )

            @job(resource_defs={'s3': s3_resource})
            def example_job(context):
                example_s3_op()

            example_job.execute_in_process(
                run_config={
                    'resources': {
                        's3': {
                            'config': {
                                'region_name': 'us-west-1',
                            }
                        }
                    }
                }
            )

    Note that your ops must also declare that they require this resource with
    `required_resource_keys`, or it will not be initialized for the execution of their compute
    functions.

    You may configure this resource as follows:

    .. code-block:: YAML

        resources:
          s3:
            config:
              region_name: "us-west-1"
              # Optional[str]: Specifies a custom region for the S3 session. Default is chosen
              # through the ordinary boto credential chain.
              use_unsigned_session: false
              # Optional[bool]: Specifies whether to use an unsigned S3 session. Default: True
              endpoint_url: "http://localhost"
              # Optional[str]: Specifies a custom endpoint for the S3 session. Default is None.
              profile_name: "dev"
              # Optional[str]: Specifies a custom profile for S3 session. Default is default
              # profile as specified in ~/.aws/credentials file

    """
    return construct_s3_client(
        max_attempts=context.resource_config["max_attempts"],
        region_name=context.resource_config.get("region_name"),
        endpoint_url=context.resource_config.get("endpoint_url"),
        use_unsigned_session=context.resource_config["use_unsigned_session"],
        profile_name=context.resource_config.get("profile_name"),
    )


@resource(
    merge_dicts(
        S3_SESSION_CONFIG,
        {
            "s3_bucket": Field(StringSource),
            "s3_prefix": Field(StringSource, is_required=False, default_value="dagster"),
        },
    )
)
def s3_file_manager(context):
    """FileManager that provides abstract access to S3.

    Implements the :py:class:`~dagster.core.storage.file_manager.FileManager` API.
    """
    return S3FileManager(
        s3_session=construct_s3_client(
            max_attempts=context.resource_config["max_attempts"],
            region_name=context.resource_config.get("region_name"),
            endpoint_url=context.resource_config.get("endpoint_url"),
            use_unsigned_session=context.resource_config["use_unsigned_session"],
            profile_name=context.resource_config.get("profile_name"),
        ),
        s3_bucket=context.resource_config["s3_bucket"],
        s3_base_key=context.resource_config["s3_prefix"],
    )
