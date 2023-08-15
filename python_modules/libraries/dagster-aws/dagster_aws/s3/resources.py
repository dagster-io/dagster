from typing import Any, Optional, TypeVar

from dagster import ConfigurableResource, IAttachDifferentObjectToOpContext, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from pydantic import Field

from .file_manager import S3FileManager
from .utils import construct_s3_client

T = TypeVar("T")


class ResourceWithS3Configuration(ConfigurableResource):
    use_unsigned_session: bool = Field(
        default=False, description="Specifies whether to use an unsigned S3 session."
    )
    region_name: Optional[str] = Field(
        default=None, description="Specifies a custom region for the S3 session."
    )
    endpoint_url: Optional[str] = Field(
        default=None, description="Specifies a custom endpoint for the S3 session."
    )
    max_attempts: int = Field(
        default=5,
        description=(
            "This provides Boto3's retry handler with a value of maximum retry attempts, where the"
            " initial call counts toward the max_attempts value that you provide."
        ),
    )
    profile_name: Optional[str] = Field(
        default=None, description="Specifies a profile to connect that session."
    )
    use_ssl: bool = Field(
        default=True, description="Whether or not to use SSL. By default, SSL is used."
    )
    verify: Optional[str] = Field(
        default=None,
        description=(
            "Whether or not to verify SSL certificates. By default SSL certificates are verified."
            " You can also specify this argument if you want to use a different CA cert bundle than"
            " the one used by botocore."
        ),
    )
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key ID to use when creating the boto3 session."
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret access key to use when creating the boto3 session."
    )
    aws_session_token: str = Field(
        default=None, description="AWS session token to use when creating the boto3 session."
    )


class S3Resource(ResourceWithS3Configuration, IAttachDifferentObjectToOpContext):
    """Resource that gives access to S3.

    The underlying S3 session is created by calling
    :py:func:`boto3.session.Session(profile_name) <boto3:boto3.session>`.
    The returned resource object is an S3 client, an instance of `botocore.client.S3`.

    Example:
        .. code-block:: python

            from dagster import job, op, Definitions
            from dagster_aws.s3 import S3Resource

            @op
            def example_s3_op(s3: S3Resource):
                return s3.get_client().list_objects_v2(
                    Bucket='my-bucket',
                    Prefix='some-key'
                )

            @job
            def example_job():
                example_s3_op()

            defs = Definitions(
                jobs=[example_job],
                resources={'s3': S3Resource(region_name='us-west-1')}
            )

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> Any:
        return construct_s3_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            endpoint_url=self.endpoint_url,
            use_unsigned_session=self.use_unsigned_session,
            profile_name=self.profile_name,
            use_ssl=self.use_ssl,
            verify=self.verify,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(config_schema=S3Resource.to_config_schema())
def s3_resource(context) -> Any:
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
    return S3Resource.from_resource_context(context).get_client()


class S3FileManagerResource(ResourceWithS3Configuration, IAttachDifferentObjectToOpContext):
    s3_bucket: str = Field(description="S3 bucket to use for the file manager.")
    s3_prefix: str = Field(
        default="dagster", description="Prefix to use for the S3 bucket for this file manager."
    )

    def get_client(self) -> S3FileManager:
        return S3FileManager(
            s3_session=construct_s3_client(
                max_attempts=self.max_attempts,
                region_name=self.region_name,
                endpoint_url=self.endpoint_url,
                use_unsigned_session=self.use_unsigned_session,
                profile_name=self.profile_name,
                use_ssl=self.use_ssl,
                verify=self.verify,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token,
            ),
            s3_bucket=self.s3_bucket,
            s3_base_key=self.s3_prefix,
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(
    config_schema=S3FileManagerResource.to_config_schema(),
)
def s3_file_manager(context) -> S3FileManager:
    """FileManager that provides abstract access to S3.

    Implements the :py:class:`~dagster._core.storage.file_manager.FileManager` API.
    """
    return S3FileManagerResource.from_resource_context(context).get_client()
