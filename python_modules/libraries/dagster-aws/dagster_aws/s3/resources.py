from dagster import Field, resource

from .utils import create_s3_session


class S3Resource(object):
    def __init__(self, s3_session):
        self.session = s3_session

    def download_file(self, bucket, key, filename, **kwargs):
        '''This mirrors the download_file boto3 API:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.download_file
        '''
        return self.session.download_file(bucket, key, filename, **kwargs)

    def download_fileobj(self, bucket, key, fileobj, **kwargs):
        '''This mirrors the download_fileobj boto3 API:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.download_fileobj
        '''
        return self.session.download_fileobj(bucket, key, fileobj, **kwargs)

    def put_object(self, **kwargs):
        '''This mirrors the put_object boto3 API:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Bucket.put_object

        The config schema for this API is applied to the put_object_to_s3_bytes solid vs. at the
        resource level here.
        '''
        return self.session.put_object(**kwargs)

    def upload_fileobj(self, fileobj, bucket, key):
        '''This mirrors the upload_file boto3 API:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.upload_fileobj
        '''
        return self.session.upload_fileobj(fileobj, bucket, key)

    def list_objects_v2(self, **kwargs):
        '''This mirrors the list_objects_v2 boto3 API:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_objects_v2
        '''
        return self.session.list_objects_v2(**kwargs)


@resource(
    {
        'use_unsigned_session': Field(
            bool,
            description='Specifies whether to use an unsigned S3 session',
            is_required=False,
            default_value=False,
        ),
        'region_name': Field(
            str, description='Specifies a custom region for the S3 session', is_required=False
        ),
        'endpoint_url': Field(
            str, description='Specifies a custom endpoint for the S3 session', is_required=False
        ),
    }
)
def s3_resource(context):
    '''Resource that gives solids access to S3.

    The underlying S3 session is created by calling :py:func:`boto3.resource('s3') <boto3:boto3.resource>`.

    Attach this resource definition to a :py:class:`~dagster.ModeDefinition` in order to make it
    available to your solids:

    .. code-block:: python

        pipeline_def = PipelineDefinition(
            mode_defs=[ModeDefinition(resource_defs={'s3': s3_resource, ...}, ...)], ...
        )

    Note that your solids must also declare that they require this resource, or it will not be
    initialized for the execution of their compute functions.

    You may configure this resource as follows:

    .. code-block:: YAML

        resources:
          s3:
            config:
              use_unsigned_session: false
              # Optional[bool]: Specifies whether to use an unsigned S3 session. Default: True
              region_name: "us-west-1"
              # Optional[str]: Specifies a custom region for the S3 session. Default is chosen
              # through the ordinary boto credential chain.
              endpoint_url: "http://localhost"
              # Optional[str]: Specifies a custom endpoint for the S3 session. Default is None.

    '''
    use_unsigned_session = context.resource_config['use_unsigned_session']
    region_name = context.resource_config.get('region_name')
    endpoint_url = context.resource_config.get('endpoint_url')
    return S3Resource(
        create_s3_session(
            signed=not use_unsigned_session, region_name=region_name, endpoint_url=endpoint_url
        )
    )
