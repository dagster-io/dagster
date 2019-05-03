import os

try:
    # Python 2 tempfile doesn't have tempfile.TemporaryDirectory
    import backports.tempfile as tempfile
except ImportError:
    import tempfile

import pytest

from dagster import execute_solid, PipelineContextDefinition, PipelineDefinition
from dagster_aws.s3.resources import s3_resource
from dagster_aws.s3.solids import download_from_s3_to_bytes, download_from_s3_to_file


@pytest.mark.nettest
def test_download_from_s3_to_file():
    with tempfile.TemporaryDirectory() as tmp_directory:
        result = execute_solid(
            PipelineDefinition(
                [download_from_s3_to_file],
                context_definitions={
                    'test': PipelineContextDefinition(resources={'s3': s3_resource})
                },
            ),
            'download_from_s3_to_file',
            environment_dict={
                'solids': {
                    'download_from_s3_to_file': {
                        'config': {
                            'bucket': 'dagster-airline-demo-source-data',
                            'key': 'test/test_file',
                            'target_folder': tmp_directory,
                            'skip_if_present': False,
                        }
                    }
                }
            },
        )
        assert result.success
        assert result.transformed_value() == os.path.join(tmp_directory, 'test_file')


@pytest.mark.nettest
def test_download_from_s3_to_bytes():
    result = execute_solid(
        PipelineDefinition(
            [download_from_s3_to_bytes],
            context_definitions={'test': PipelineContextDefinition(resources={'s3': s3_resource})},
        ),
        'download_from_s3_to_bytes',
        environment_dict={
            'solids': {
                'download_from_s3_to_bytes': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'test/test_file',
                    }
                }
            }
        },
    )
    assert result.success
    assert result.transformed_value().read() == b'test\n'
