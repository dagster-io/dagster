from dagster import (
    solid,
    Bool,
    Bytes,
    Dict,
    Field,
    InputDefinition,
    OutputDefinition,
    Path,
    Result,
    String,
)

from .configs import put_object_configs
from .types import FileExistsAtPath


@solid(
    name='download_from_s3_to_bytes',
    config_field=Field(
        Dict(
            fields={
                'bucket': Field(String, description='S3 bucket name'),
                'key': Field(String, description='S3 key name'),
            }
        )
    ),
    description='Downloads an object from S3.',
    outputs=[OutputDefinition(Bytes, description='The contents of the downloaded object.')],
    resources={'s3'},
)
def download_from_s3_to_bytes(context):
    '''Download an object from S3 as an in-memory bytes object.

    Returns:
        str:
            The path to the downloaded object.
    '''
    (bucket, key) = (context.solid_config.get(k) for k in ('bucket', 'key'))

    return context.resources.s3.download_from_s3_to_bytes(bucket, key)


@solid(
    name='download_from_s3_to_file',
    config_field=Field(
        Dict(
            fields={
                'bucket': Field(String, description='S3 bucket name'),
                'key': Field(String, description='S3 key name'),
                'target_folder': Field(
                    Path, description=('Specifies the path at which to download the object.')
                ),
                'skip_if_present': Field(Bool, is_optional=True, default_value=False),
            }
        )
    ),
    description='Downloads an object from S3 to a file.',
    outputs=[OutputDefinition(FileExistsAtPath, description='The path to the downloaded object.')],
    resources={'s3'},
)
def download_from_s3_to_file(context):
    '''Download an object from S3 to a local file.
    '''
    (bucket, key, target_folder, skip_if_present) = (
        context.solid_config.get(k) for k in ('bucket', 'key', 'target_folder', 'skip_if_present')
    )

    return context.resources.s3.download_from_s3_to_file(
        context, bucket, key, target_folder, skip_if_present
    )


@solid(
    name='put_object_to_s3_bytes',
    config_field=put_object_configs(),
    inputs=[InputDefinition('file_obj', Bytes, description='The file to upload.')],
    description='Uploads a file to S3.',
    outputs=[
        OutputDefinition(
            String, description='The bucket to which the file was uploaded.', name='bucket'
        ),
        OutputDefinition(String, description='The key to which the file was uploaded.', name='key'),
    ],
    resources={'s3'},
)
def put_object_to_s3_bytes(context, file_obj):
    '''Upload file contents to s3.

    Args:
        file_obj (Bytes): The bytes of a file object.

    Returns:
        (str, str):
            The bucket and key to which the file was uploaded.
    '''
    bucket = context.solid_config['Bucket']
    key = context.solid_config['Key']

    # the s3 put_object API expects the actual bytes to be on the 'Body' key in kwargs; since we
    # get all other fields from config, we copy the config object and add 'Body' here.
    cfg = context.solid_config.copy()
    cfg['Body'] = file_obj.read()

    context.resources.s3.put_object(**cfg)

    yield Result(bucket, 'bucket')
    yield Result(key, 'key')
