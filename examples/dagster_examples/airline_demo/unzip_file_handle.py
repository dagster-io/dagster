import zipfile

from dagster import solid, InputDefinition, FileHandle, String, OutputDefinition


@solid(
    inputs=[
        InputDefinition('archive_file_handle', FileHandle),
        InputDefinition('archive_member', String),
    ],
    outputs=[OutputDefinition(FileHandle)],
    description='''Unzip a file that is resident in an archive file as a member.
    This solid operates on FileHandles, meaning that their physical is dependent
    on what system storage is operating in the pipeline. The physical file could
    be on local disk, or it could be in s3. If on s3, this solid will download
    that file to local disk, perform the unzip, upload that file back to s3, and
    then return that file handle for downstream use in the computations.
    ''',
)
def unzip_file_handle(context, archive_file_handle, archive_member):
    with context.file_manager.read(archive_file_handle, mode='rb') as local_obj:
        with zipfile.ZipFile(local_obj) as zip_file:
            with zip_file.open(archive_member) as unzipped_stream:
                return context.file_manager.write(unzipped_stream, mode='wb')
