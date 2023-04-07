from dagster import Field, Noneable, StringSource, resource
from dagster._utils.merger import merge_dicts

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
        description=(
            "This provides Boto3's retry handler with a value of maximum retry attempts, "
            "where the initial call counts toward the max_attempts value that you provide"
        ),
        is_required=False,
        default_value=5,
    ),
    "profile_name": Field(
        str,
        description="Specifies a profile to connect that session",
        is_required=False,
    ),
    "use_ssl": Field(
        bool,
        description="Whether or not to use SSL. By default, SSL is used.",
        is_required=False,
        default_value=True,
    ),
    "verify": Field(
        Noneable(str),
        description=(
            "Whether or not to verify SSL certificates. By default SSL certificates are verified."
            " You can also specify this argument if you want to use a different CA cert bundle than"
            " the one used by botocore."
        ),
        is_required=False,
        default_value=None,
    ),
    "aws_access_key_id": Field(
        Noneable(StringSource),
        description="The access key to use when creating the client.",
        is_required=False,
        default_value=None,
    ),
    "aws_secret_access_key": Field(
        Noneable(StringSource),
        description="The secret key to use when creating the client.",
        is_required=False,
        default_value=None,
    ),
    "aws_session_token": Field(
        Noneable(StringSource),
        description="The session token to use when creating the client.",
        is_required=False,
        default_value=None,
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
            def example_job():
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
              use_ssl: true
              # Optional[bool]: Whether or not to use SSL. By default, SSL is used.
              verify: None
              # Optional[str]: Whether or not to verify SSL certificates. By default SSL certificates are verified.
              # You can also specify this argument if you want to use a different CA cert bundle than the one used by botocore."
              aws_access_key_id: None
              # Optional[str]: The access key to use when creating the client.
              aws_secret_access_key: None
              # Optional[str]: The secret key to use when creating the client.
              aws_session_token: None
              # Optional[str]:  The session token to use when creating the client.
    """
    return construct_s3_client(
        max_attempts=context.resource_config["max_attempts"],
        region_name=context.resource_config.get("region_name"),
        endpoint_url=context.resource_config.get("endpoint_url"),
        use_unsigned_session=context.resource_config["use_unsigned_session"],
        profile_name=context.resource_config.get("profile_name"),
        use_ssl=context.resource_config.get("use_ssl"),
        verify=context.resource_config.get("verify"),
        aws_access_key_id=context.resource_config.get("aws_access_key_id"),
        aws_secret_access_key=context.resource_config.get("aws_secret_access_key"),
        aws_session_token=context.resource_config.get("aws_session_token"),
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

    Implements the :py:class:`~dagster._core.storage.file_manager.FileManager` API.
    """
    return S3FileManager(
        s3_session=construct_s3_client(
            max_attempts=context.resource_config["max_attempts"],
            region_name=context.resource_config.get("region_name"),
            endpoint_url=context.resource_config.get("endpoint_url"),
            use_unsigned_session=context.resource_config["use_unsigned_session"],
            profile_name=context.resource_config.get("profile_name"),
            use_ssl=context.resource_config.get("use_ssl"),
            verify=context.resource_config.get("verify"),
            aws_access_key_id=context.resource_config.get("aws_access_key_id"),
            aws_secret_access_key=context.resource_config.get("aws_secret_access_key"),
            aws_session_token=context.resource_config.get("aws_session_token"),
        ),
        s3_bucket=context.resource_config["s3_bucket"],
        s3_base_key=context.resource_config["s3_prefix"],
    )
