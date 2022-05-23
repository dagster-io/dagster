import os

from dagster import AssetKey, AssetMaterialization, Field, MetadataValue, Output, graph, op


@op(
    config_schema={
        "filename": Field(str, is_required=True),
        "directory": Field(str, is_required=True),
    }
)
def read_file(context):
    relative_filename = context.op_config["filename"]
    directory = context.op_config["directory"]
    filename = os.path.join(directory, relative_filename)
    try:
        fstats = os.stat(filename)
        context.log.info("Found file {}".format(relative_filename))
        yield AssetMaterialization(
            asset_key=AssetKey(["log_file", relative_filename]),
            metadata={
                "path": MetadataValue.path(filename),
                "File status": {
                    "size": fstats.st_size,
                    "ctime": fstats.st_ctime,
                    "mtime": fstats.st_mtime,
                },
            },
        )
        yield Output(relative_filename)
    except FileNotFoundError:
        context.log.error("No file found: {}".format(relative_filename))


@graph
def log_file():
    read_file()


log_file_job = log_file.to_job(description="Demo job that spits out some file info, given a path")
