from dagster import (
    FileHandle,
    Bool,
    Dict,
    Field,
    InputDefinition,
    OutputDefinition,
    Path,
    Materialization,
    Result,
    String,
    check,
    input_schema,
    solid,
)

from .configs import put_object_configs
from .file_manager import S3FileHandle
from .types import FileExistsAtPath

from dagster.core.types.runtime import PythonObjectType


def dict_with_fields(name, fields):
    check.str_param(name, 'name')
    check.dict_param(fields, 'fields', key_type=str)
    field_names = set(fields.keys())

    @input_schema(Dict(fields))
    def _input_schema(_context, value):
        check.dict_param(value, 'value')
        check.param_invariant(set(value.keys()) == field_names, 'value')
        return value

    class _DictWithSchema(PythonObjectType):
        def __init__(self):
            super(_DictWithSchema, self).__init__(
                python_type=dict, name=name, input_schema=_input_schema
            )

    return _DictWithSchema


S3BucketData = dict_with_fields(
    'S3BucketData',
    fields={
        'bucket': Field(String, description='S3 bucket name'),
        'key': Field(String, description='S3 key name'),
    },
)


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
    required_resources={'s3'},
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
    config_field=put_object_configs(),
    inputs=[InputDefinition('file_handle', FileHandle, description='The file to upload.')],
    outputs=[OutputDefinition(name='s3_file_handle', dagster_type=S3FileHandle)],
    description='''Take a file handle and upload it to s3. See configuration for all
    arguments you can pass to put_object. Returns an S3FileHandle.''',
)
def file_handle_to_s3(context, file_handle):
    bucket = context.solid_config['Bucket']
    key = context.solid_config['Key']

    # the s3 put_object API expects the actual bytes to be on the 'Body' key in kwargs; since we
    # get all other fields from config, we copy the config object and add 'Body' here.
    cfg = context.solid_config.copy()
    with context.file_manager.read(file_handle, 'rb') as file_obj:
        cfg['Body'] = file_obj

        context.resources.s3.put_object(**cfg)
        s3_file_handle = S3FileHandle(bucket, key)

        yield Materialization(path=s3_file_handle.s3_path)

        yield Result(value=s3_file_handle, output_name='s3_file_handle')
