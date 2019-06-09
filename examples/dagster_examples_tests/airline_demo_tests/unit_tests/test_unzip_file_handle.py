import sys
import zipfile

from dagster import solid, pipeline, LocalFileHandle, execute_pipeline
from dagster.utils.test import get_temp_file_name
from dagster_examples.airline_demo.solids import unzip_file_handle


# for dep graphs
# pylint: disable=no-value-for-parameter


def test_unzip_file_handle():
    data = 'foo'.encode()

    with get_temp_file_name() as zip_file_name:

        with zipfile.ZipFile(zip_file_name, mode='w') as archive:
            # writable stream with archive.open not available < 3.6
            kwargs = (
                {'bytes': data, 'zinfo_or_arcname': 'some_archive_member'}
                if sys.version_info.major < 3
                else {'data': data, 'zinfo_or_arcname': 'some_archive_member'}
            )

            archive.writestr(**kwargs)

        @solid
        def to_zip_file_handle(_):
            return LocalFileHandle(zip_file_name)

        @pipeline
        def do_test_unzip_file_handle(_):
            return unzip_file_handle(to_zip_file_handle())

        result = execute_pipeline(
            do_test_unzip_file_handle,
            environment_dict={
                'solids': {
                    'unzip_file_handle': {
                        'inputs': {'archive_member': {'value': 'some_archive_member'}}
                    }
                }
            },
        )
        assert result.success
