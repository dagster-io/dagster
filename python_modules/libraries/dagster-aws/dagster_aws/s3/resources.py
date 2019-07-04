from dagster import Field, resource

from .utils import create_s3_session


class S3Resource:
    def __init__(self, s3_session):
        self.session = s3_session

    def put_object(self, **kwargs):
        '''This mirrors the put_object boto3 API:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Bucket.put_object

        The config schema for this API is applied to the put_object_to_s3_bytes solid vs. at the
        resource level here.
        '''
        return self.session.put_object(**kwargs)


@resource(
    {
        'use_unsigned_session': Field(
            bool,
            description='Specifies whether to use an unsigned S3 session',
            is_optional=True,
            default_value=True,
        )
    }
)
def s3_resource(context):
    use_unsigned_session = context.resource_config['use_unsigned_session']
    return S3Resource(create_s3_session(signed=not use_unsigned_session))
