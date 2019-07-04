from dagster import (
    EventMetadataEntry,
    FileHandle,
    Dict,
    Field,
    InputDefinition,
    OutputDefinition,
    Materialization,
    Output,
    String,
    check,
    input_hydration_config,
    solid,
)

from .configs import put_object_configs
from .file_manager import S3FileHandle

from dagster.core.types.runtime import PythonObjectType


def dict_with_fields(name, fields):
    check.str_param(name, 'name')
    check.dict_param(fields, 'fields', key_type=str)
    field_names = set(fields.keys())

    @input_hydration_config(Dict(fields))
    def _input_schema(_context, value):
        check.dict_param(value, 'value')
        check.param_invariant(set(value.keys()) == field_names, 'value')
        return value

    class _DictWithSchema(PythonObjectType):
        def __init__(self):
            super(_DictWithSchema, self).__init__(
                python_type=dict, name=name, input_hydration_config=_input_schema
            )

    return _DictWithSchema


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
    config_field=put_object_configs(),
    input_defs=[InputDefinition('file_handle', FileHandle, description='The file to upload.')],
    output_defs=[OutputDefinition(name='s3_file_handle', dagster_type=S3FileHandle)],
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

        yield Materialization(
            label='file_to_s3',
            metadata_entries=[EventMetadataEntry.path(s3_file_handle.s3_path, label=last_key(key))],
        )

        yield Output(value=s3_file_handle, output_name='s3_file_handle')
