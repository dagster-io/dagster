from dagster import (
    Dict,
    ExpectationResult,
    Field,
    InputDefinition,
    OutputDefinition,
    Result,
    String,
    solid,
)
from dagster.utils.test import get_temp_file_name

from dagster_aws.s3.solids import S3BucketData

from .keyed_file_store import FileHandle


@solid(
    inputs=[InputDefinition('bucket_data', S3BucketData)],
    outputs=[OutputDefinition(FileHandle)],
    config_field=Field(
        Dict(
            {
                'file_key': Field(
                    String,
                    is_optional=True,
                    description=(
                        'Optionally specify the key for the file to be ingested '
                        'into the keyed store. Defaults to the last path component '
                        'of the downloaded s3 key.'
                    ),
                )
            }
        )
    ),
    required_resources={'keyed_file_store', 's3'},
    description='''This is a solid which mirrors a file in s3 into a keyed file store.
    The keyed file store is a resource type that allows a solid author to save files
    and assign a key to them. The keyed file store can be backed by local file or any
    object store (currently we support s3). This keyed file store can be configured
    to be at an external location so that is persists in a well known spot between runs.
    It is designed for the case where there is an expensive download step that should not
    occur unless the downloaded file does not exist. Redownload can be instigated either
    by configuring the source to overwrite files or to just delete the file in the underlying
    storage manually.

    This works by downloading the file to a temporary file, and then ingesting it into
    the keyed file store. In the case of a filesystem-backed key store, this is a file
    copy. In the case of a object-store-backed key store, this is an upload.

    In order to work this must be executed within a mode that provides an s3
    and keyed_file_store resource.
    ''',
)
def mirror_keyed_file_from_s3(context, bucket_data):
    target_key = context.solid_config.get('file_key', bucket_data['key'].split('/')[-1])

    keyed_file_store = context.resources.keyed_file_store

    file_handle = keyed_file_store.get_file_handle(target_key)

    if keyed_file_store.overwrite or not keyed_file_store.has_file_object(target_key):

        with get_temp_file_name() as tmp_file:
            context.resources.s3.session.download_file(
                Bucket=bucket_data['bucket'], Key=bucket_data['key'], Filename=tmp_file
            )

            context.log.info('File downloaded to {}'.format(tmp_file))

            with open(tmp_file, 'rb') as tmp_file_object:
                keyed_file_store.write_file_object(target_key, tmp_file_object)
                context.log.info('File handle written at : {}'.format(file_handle.path_desc))
    else:
        context.log.info('File {} already present in keyed store'.format(file_handle.path_desc))

    yield ExpectationResult(
        success=keyed_file_store.has_file_object(target_key),
        name='file_handle_exists',
        result_metadata={'path': file_handle.path_desc},
    )
    yield Result(file_handle)
