import os

from dagster import (
    AssetKey,
    AssetMaterialization,
    EventMetadataEntry,
    Field,
    Output,
    pipeline,
    solid,
)


@solid(
    config_schema={
        "filename": Field(str, is_required=True),
        "directory": Field(str, is_required=True),
    }
)
def read_file(context):
    relative_filename = context.solid_config["filename"]
    directory = context.solid_config["directory"]
    filename = os.path.join(directory, relative_filename)
    try:
        fstats = os.stat(filename)
        context.log.info("Found file {}".format(relative_filename))
        yield AssetMaterialization(
            asset_key=AssetKey(["log_file", relative_filename]),
            metadata_entries=[
                EventMetadataEntry.fspath(filename),
                EventMetadataEntry.json(
                    {
                        "size": fstats.st_size,
                        "ctime": fstats.st_ctime,
                        "mtime": fstats.st_mtime,
                    },
                    "File stats",
                ),
            ],
        )
        yield Output(relative_filename)
    except FileNotFoundError:
        context.log.error("No file found: {}".format(relative_filename))


@pipeline(description="Demo pipeline that spits out some file info, given a path")
def log_file_pipeline():
    read_file()
