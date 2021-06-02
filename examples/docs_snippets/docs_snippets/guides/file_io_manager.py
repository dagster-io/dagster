"""isort:skip_file"""

# solids_start
import os
import uuid
from pathlib import Path

from dagster import (
    solid,
    OutputDefinition,
)


def unique_file_path(directory):
    return Path(directory) / str(uuid.uuid4())


@solid(
    required_resource_keys={"tempdir"},
    output_defs=[OutputDefinition(metadata={"persistent_path_suffix": "some_dir/abc_file"})],
)
def create_file(context) -> Path:
    tmpfile = unique_file_path(context.resources.tempdir)
    os.system(f"echo abc > {tmpfile}")
    return tmpfile


@solid(
    required_resource_keys={"tempdir"},
    output_defs=[OutputDefinition(metadata={"persistent_path_suffix": "some_dir/count_file"})],
)
def count_characters(context, local_path: Path) -> Path:
    tmpfile = unique_file_path(context.resources.tempdir)
    os.system(f"wc -c {local_path} > {tmpfile}")
    return tmpfile


# solids_end


# s3_io_manager_start
import boto3
from dagster import (
    IOManager,
    io_manager,
    AssetKey,
)


def s3_client():
    return boto3.resource("s3", use_ssl=True).meta.client


class S3FileIOManager(IOManager):
    def handle_output(self, context, obj: Path):
        s3_client().upload_file(str(obj), "my_bucket", context.metadata["persistent_path_suffix"])

    def load_input(self, context):
        tmpfile = unique_file_path(context.resources.tempdir)
        s3_client().download_file(
            Bucket="my_bucket",
            Key=context.upstream_output.metadata["persistent_path_suffix"],
            Filename=str(tmpfile),
        )
        return tmpfile

    def get_output_asset_key(self, context):
        return AssetKey(["my_bucket", context.metadata["persistent_path_suffix"]])


@io_manager(required_resource_keys={"tempdir"})
def s3_file_io_manager(_):
    return S3FileIOManager()


# s3_io_manager_end


# local_io_manager_start
import shutil


class LocalFileIOManager(IOManager):
    def handle_output(self, context, obj: Path):
        persistent_path = Path("base_dir") / context.metadata["persistent_path_suffix"]
        persistent_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(obj, persistent_path)

    def load_input(self, context):
        persistent_path = (
            Path("base_dir") / context.upstream_output.metadata["persistent_path_suffix"]
        )
        tmpfile = unique_file_path(context.resources.tempdir)
        shutil.copy(persistent_path, tmpfile)
        return tmpfile


@io_manager(required_resource_keys={"tempdir"})
def local_file_io_manager(_):
    return LocalFileIOManager()


# local_io_manager_end

# tempdir_start
from dagster import resource
from tempfile import TemporaryDirectory


@resource
def tempdir(_):
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


# tempdir_end


# pipeline_start
from dagster import pipeline, ModeDefinition


@pipeline(
    mode_defs=[
        ModeDefinition(
            "prod", resource_defs={"tempdir": tempdir, "io_manager": s3_file_io_manager}
        ),
        ModeDefinition(
            "dev", resource_defs={"tempdir": tempdir, "io_manager": local_file_io_manager}
        ),
    ]
)
def file_pipeline():
    count_characters(create_file())


# pipeline_end
