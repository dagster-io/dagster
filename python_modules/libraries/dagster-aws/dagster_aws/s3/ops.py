from collections.abc import Generator, Mapping
from typing import Any

from dagster import (
    AssetMaterialization,
    Field,
    FileHandle,
    In,
    MetadataValue,
    Out,
    Output,
    StringSource,
    _check as check,
    dagster_type_loader,
    op,
)
from dagster._core.types.dagster_type import PythonObjectDagsterType

from dagster_aws.s3.file_manager import S3FileHandle


def dict_with_fields(name: str, fields: Mapping[str, object]):
    check.str_param(name, "name")
    check.mapping_param(fields, "fields", key_type=str)
    field_names = set(fields.keys())

    @dagster_type_loader(fields)
    def _input_schema(_context, value):
        check.dict_param(value, "value")
        check.param_invariant(set(value.keys()) == field_names, "value")
        return value

    class _DictWithSchema(PythonObjectDagsterType):
        def __init__(self):
            super().__init__(python_type=dict, name=name, loader=_input_schema)

    return _DictWithSchema()


S3Coordinate = dict_with_fields(
    "S3Coordinate",
    fields={
        "bucket": Field(StringSource, description="S3 bucket name"),
        "key": Field(StringSource, description="S3 key name"),
    },
)


def last_key(key: str) -> str:
    if "/" not in key:
        return key
    comps = key.split("/")
    return comps[-1]


@op(
    config_schema={
        "Bucket": Field(
            StringSource, description="The name of the bucket to upload to.", is_required=True
        ),
        "Key": Field(
            StringSource, description="The name of the key to upload to.", is_required=True
        ),
    },
    ins={"file_handle": In(FileHandle, description="The file to upload.")},
    out={"s3_file_handle": Out(S3FileHandle)},
    description="""Take a file handle and upload it to s3. Returns an S3FileHandle.""",
    required_resource_keys={"s3", "file_manager"},
)
def file_handle_to_s3(context, file_handle) -> Generator[Any, None, None]:
    bucket = context.op_config["Bucket"]
    key = context.op_config["Key"]

    file_manager = context.resources.file_manager
    s3 = context.resources.s3

    with file_manager.read(file_handle, "rb") as fileobj:
        s3.upload_fileobj(fileobj, bucket, key)
        s3_file_handle = S3FileHandle(bucket, key)

        yield AssetMaterialization(
            asset_key=s3_file_handle.s3_path,
            metadata={last_key(key): MetadataValue.path(s3_file_handle.s3_path)},
        )

        yield Output(value=s3_file_handle, output_name="s3_file_handle")
