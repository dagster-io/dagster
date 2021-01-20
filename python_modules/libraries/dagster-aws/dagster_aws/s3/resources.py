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
}


@resource(S3_SESSION_CONFIG)
def s3_resource(context):
    """Resource that gives solids access to S3.

    The underlying S3 session is created by calling :py:func:`boto3.resource('s3') <boto3:boto3.resource>`.

    Attach this resource definition to a :py:class:`~dagster.ModeDefinition` in order to make it
    available to your solids.

    Example:

        .. code-block:: python

            from dagster import ModeDefinition, execute_solid, solid
            from dagster_aws.s3 import s3_resource

            @solid(required_resource_keys={'s3'})
            def example_s3_solid(context):
                return context.resources.s3.list_objects_v2(
                    Bucket='my-bucket',
                    Prefix='some-key'
                )

            result = execute_solid(
                example_s3_solid,
                run_config={
                    'resources': {
                        's3': {
                            'config': {
                                'region_name': 'us-west-1',
                            }
                        }
                    }
                },
                mode_def=ModeDefinition(resource_defs={'s3': s3_resource}),
            )

    Note that your solids must also declare that they require this resource with
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
    """
    return construct_s3_client(
        max_attempts=context.resource_config["max_attempts"],
        region_name=context.resource_config.get("region_name"),
        endpoint_url=context.resource_config.get("endpoint_url"),
        use_unsigned_session=context.resource_config["use_unsigned_session"],
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
        ),
        s3_bucket=context.resource_config["s3_bucket"],
        s3_base_key=context.resource_config["s3_prefix"],
    )
