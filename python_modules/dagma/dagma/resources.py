"""Resource definition for dagma."""
from collections import namedtuple

import boto3

from dagster import ResourceDefinition, types

from .config import DEFAULT_S3_BUCKET, DEFAULT_STORAGE_CONFIG, DEFAULT_RUNTIME_BUCKET
from .storage import Storage

DagmaResourceConfig = types.Dict(
    {
        'aws_access_key_id': types.Field(types.String, is_optional=True),
        'aws_secret_access_key': types.Field(types.String, is_optional=True),
        'aws_session_token': types.Field(types.String, is_optional=True),
        'aws_region_name': types.Field(types.String),
        's3_bucket': types.Field(types.String, default_value=DEFAULT_S3_BUCKET, is_optional=True),
        'runtime_bucket': types.Field(
            types.String, default_value=DEFAULT_RUNTIME_BUCKET, is_optional=True
        ),
        # 'cleanup_lambda_functions': types.Field(types.Bool, default_value=False,
        #                                         is_optional=True),  # TODO: Thread this through
        # TODO also parametrize local tempfile cleanup
        # TODO also parametrize s3 cleanup
        # TODO use config to pass nested typed kwargs to aws clients
    }
)
"""The dagma resource config type."""


class DagmaResourceType(
    namedtuple(
        '_AwsLambdaExecutionInfo', 'sessionmaker aws_region_name storage s3_bucket runtime_bucket'
    )
):
    """The dagma resource type."""

    @property
    def session(self):
        """The boto3 session."""
        return self.sessionmaker()


def define_dagma_resource():
    """Returns a ResourceDefinition appropriate for use of the dagma engine.

    Usage:

        from dagster import PipelineContextDefinition

        PipelineContextDefinition(
            ...,
            resources={
                ...,
                'dagma': define_dagma_resource(),
            },
        )
    """

    def _create_dagma_resource(info):
        sessionmaker = lambda: boto3.Session(  # Otherwise, can't be pickled b/c of ssl.SSLContext
            aws_access_key_id=info.config.get('aws_access_key_id'),
            aws_secret_access_key=info.config.get('aws_secret_access_key'),
            aws_session_token=info.config.get('aws_session_token'),
            region_name=info.config['aws_region_name'],
        )

        storage_config = dict(
            DEFAULT_STORAGE_CONFIG, sessionmaker=sessionmaker, s3_bucket=info.config['s3_bucket']
        )

        return DagmaResourceType(
            sessionmaker=sessionmaker,
            aws_region_name=info.config['aws_region_name'],
            storage=Storage(storage_config),
            s3_bucket=info.config['s3_bucket'],
            runtime_bucket=info.config['runtime_bucket'],
        )

    return ResourceDefinition(
        resource_fn=_create_dagma_resource, config_field=types.Field(DagmaResourceConfig)
    )
