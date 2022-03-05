from dagster_aws.s3 import S3Coordinate

from dagster import ExpectationResult, Field, FileHandle, MetadataEntry, Output, solid
from dagster.utils.temp_file import get_temp_file_name


@solid(
    config_schema={
        "file_key": Field(
            str,
            is_required=False,
            description=(
                "Optionally specify the key for the file to be ingested "
                "into the keyed store. Defaults to the last path component "
                "of the downloaded s3 key."
            ),
        )
    },
    required_resource_keys={"file_cache", "s3"},
    description="""This is a solid which caches a file in s3 into file cache.

The `file_cache` is a resource type that allows a solid author to save files
and assign a key to them. The keyed file store can be backed by local file or any
object store (currently we support s3). This keyed file store can be configured
to be at an external location so that is persists in a well known spot between runs.
It is designed for the case where there is an expensive download step that should not
occur unless the downloaded file does not exist. Redownload can be instigated either
by configuring the source to overwrite files or to just delete the file in the underlying
storage manually.

This works by downloading the file to a temporary file, and then ingesting it into
the file cache. In the case of a filesystem-backed file cache, this is a file
copy. In the case of a object-store-backed file cache, this is an upload.

In order to work this must be executed within a mode that provides an `s3`
and `file_cache` resource.
    """,
)
def cache_file_from_s3(context, s3_coordinate: S3Coordinate) -> FileHandle:
    target_key = context.solid_config.get("file_key", s3_coordinate["key"].split("/")[-1])

    file_cache = context.resources.file_cache

    target_file_handle = file_cache.get_file_handle(target_key)

    if file_cache.overwrite or not file_cache.has_file_object(target_key):
        with get_temp_file_name() as tmp_file:
            context.resources.s3.download_file(
                Bucket=s3_coordinate["bucket"], Key=s3_coordinate["key"], Filename=tmp_file
            )

            context.log.info("File downloaded to {}".format(tmp_file))

            with open(tmp_file, "rb") as tmp_file_object:
                file_cache.write_file_object(target_key, tmp_file_object)
                context.log.info("File handle written at : {}".format(target_file_handle.path_desc))
    else:
        context.log.info("File {} already present in cache".format(target_file_handle.path_desc))

    yield ExpectationResult(
        success=file_cache.has_file_object(target_key),
        label="file_handle_exists",
        metadata_entries=[MetadataEntry.path(path=target_file_handle.path_desc, label=target_key)],
    )
    yield Output(target_file_handle)
