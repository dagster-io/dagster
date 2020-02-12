from dagster import (
    EventMetadataEntry,
    Field,
    FileHandle,
    InputDefinition,
    Materialization,
    Output,
    OutputDefinition,
    String,
    check,
    input_hydration_config,
    solid,
)
from dagster.core.types.dagster_type import PythonObjectDagsterType

from .file_manager import S3FileHandle


def dict_with_fields(name, fields):
    check.str_param(name, 'name')
    check.dict_param(fields, 'fields', key_type=str)
    field_names = set(fields.keys())

    @input_hydration_config(fields)
    def _input_schema(_context, value):
        check.dict_param(value, 'value')
        check.param_invariant(set(value.keys()) == field_names, 'value')
        return value

    class _DictWithSchema(PythonObjectDagsterType):
        def __init__(self):
            super(_DictWithSchema, self).__init__(
                python_type=dict, name=name, input_hydration_config=_input_schema
            )

    return _DictWithSchema()


S3Coordinate = dict_with_fields(
    'S3Coordinate',
    fields={
        'bucket': Field(String, description='S3 bucket name'),
        'key': Field(String, description='S3 key name'),
    },
)


def last_key(key):
    if '/' not in key:
        return key
    comps = key.split('/')
    return comps[-1]


@solid(
    config={
        'Bucket': Field(
            String, description='The name of the bucket to upload to.', is_required=True
        ),
        'Key': Field(String, description='The name of the key to upload to.', is_required=True),
    },
    input_defs=[InputDefinition('file_handle', FileHandle, description='The file to upload.')],
    output_defs=[OutputDefinition(name='s3_file_handle', dagster_type=S3FileHandle)],
    description='''Take a file handle and upload it to s3. Returns an S3FileHandle.''',
    required_resource_keys={'s3'},
)
def file_handle_to_s3(context, file_handle):
    bucket = context.solid_config['Bucket']
    key = context.solid_config['Key']

    with context.file_manager.read(file_handle, 'rb') as fileobj:
        context.resources.s3.upload_fileobj(fileobj, bucket, key)
        s3_file_handle = S3FileHandle(bucket, key)

        yield Materialization(
            label='file_to_s3',
            metadata_entries=[EventMetadataEntry.path(s3_file_handle.s3_path, label=last_key(key))],
        )

        yield Output(value=s3_file_handle, output_name='s3_file_handle')
