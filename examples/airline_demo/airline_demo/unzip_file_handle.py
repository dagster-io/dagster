import zipfile

from dagster import FileHandle, String, solid


@solid(
    description="""Unzip a file that is resident in an archive file as a member.
    This solid operates on FileHandles, meaning that their physical is dependent
    on what system storage is operating in the pipeline. The physical file could
    be on local disk, or it could be in s3. If on s3, this solid will download
    that file to local disk, perform the unzip, upload that file back to s3, and
    then return that file handle for downstream use in the computations.
    """,
    required_resource_keys={"file_manager"},
)
def unzip_file_handle(
    context, archive_file_handle: FileHandle, archive_member: String
) -> FileHandle:
    with context.resources.file_manager.read(archive_file_handle) as local_obj:
        with zipfile.ZipFile(local_obj) as zip_file:
            # boto requires a file object with seek(), but zip_file.open() would return a
            # stream without seek(), so stage on the local filesystem first
            local_extracted_path = zip_file.extract(archive_member)
            with open(local_extracted_path, "rb", encoding="utf8") as local_extracted_file:
                return context.resources.file_manager.write(local_extracted_file)
