"""Pipeline definitions for the airline_demo."""

import gzip
import os
import shutil

from dagster import (
    Bool,
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    List,
    ModeDefinition,
    OutputDefinition,
    Path,
    PipelineDefinition,
    SolidInvocation,
    String,
    lambda_solid,
    solid,
)
from dagster.core.types.runtime import Stringish
from dagster.utils import safe_isfile, mkdir_p

from dagster_aws.s3.resources import s3_resource
from dagster_aws.s3.utils import S3Logger
from dagster_snowflake import snowflake_resource, SnowflakeLoadSolidDefinition
from dagster_spark import SparkSolidDefinition


class FileExistsAtPath(Stringish):
    def __init__(self):
        super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

    def coerce_runtime_value(self, value):
        value = super(FileExistsAtPath, self).coerce_runtime_value(value)
        return self.throw_if_false(safe_isfile, value)


def _download_from_s3_to_file(session, context, bucket, key, target_folder, skip_if_present):
    # TODO: remove context argument once we support resource logging

    # file name is S3 key path suffix after last /
    target_file = os.path.join(target_folder, key.split('/')[-1])

    if skip_if_present and safe_isfile(target_file):
        context.log.info(
            'Skipping download, file already present at {target_file}'.format(
                target_file=target_file
            )
        )
    else:
        if not os.path.exists(target_folder):
            mkdir_p(target_folder)

        context.log.info(
            'Starting download of {bucket}/{key} to {target_file}'.format(
                bucket=bucket, key=key, target_file=target_file
            )
        )

        headers = session.head_object(Bucket=bucket, Key=key)
        logger = S3Logger(
            context.log.debug, bucket, key, target_file, int(headers['ContentLength'])
        )
        session.download_file(Bucket=bucket, Key=key, Filename=target_file, Callback=logger)
    return target_file


# This should be ported to use FileHandle-based solids.
# See https://github.com/dagster-io/dagster/issues/1476
@solid(
    name='download_from_s3_to_file',
    config_field=Field(
        Dict(
            fields={
                'bucket': Field(String, description='S3 bucket name'),
                'key': Field(String, description='S3 key name'),
                'target_folder': Field(
                    Path, description=('Specifies the path at which to download the object.')
                ),
                'skip_if_present': Field(Bool, is_optional=True, default_value=False),
            }
        )
    ),
    description='Downloads an object from S3 to a file.',
    outputs=[OutputDefinition(FileExistsAtPath, description='The path to the downloaded object.')],
    required_resources={'s3'},
)
def download_from_s3_to_file(context):
    '''Download an object from S3 to a local file.
    '''
    (bucket, key, target_folder, skip_if_present) = (
        context.solid_config.get(k) for k in ('bucket', 'key', 'target_folder', 'skip_if_present')
    )

    return _download_from_s3_to_file(
        context.resources.s3.session, context, bucket, key, target_folder, skip_if_present
    )


@lambda_solid(inputs=[InputDefinition('gzip_file', String)], output=OutputDefinition(List[String]))
def gunzipper(gzip_file):
    '''gunzips /path/to/foo.gz to /path/to/raw/2019/01/01/data.json
    '''
    # TODO: take date as an input

    path_prefix = os.path.dirname(gzip_file)
    output_folder = os.path.join(path_prefix, 'raw/2019/01/01')
    outfile = os.path.join(output_folder, 'data.json')

    if not safe_isfile(outfile):
        mkdir_p(output_folder)

        with gzip.open(gzip_file, 'rb') as f_in, open(outfile, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return [path_prefix]


def define_event_ingest_pipeline():
    event_ingest = SparkSolidDefinition(
        name='event_ingest',
        main_class='io.dagster.events.EventPipeline',
        description='Ingest events from JSON to Parquet',
    )

    # TODO: express dependency of this solid on event_ingest
    snowflake_load = SnowflakeLoadSolidDefinition(
        'snowflake_load',
        # TODO: need to pull this out to a config
        src='file:///tmp/dagster/events/data/output/2019/01/01/*.parquet',
        table='events',
    )

    return PipelineDefinition(
        name='event_ingest_pipeline',
        solid_defs=[download_from_s3_to_file, gunzipper, event_ingest, snowflake_load],
        dependencies={
            SolidInvocation('gunzipper'): {
                'gzip_file': DependencyDefinition('download_from_s3_to_file')
            },
            SolidInvocation('event_ingest'): {'spark_inputs': DependencyDefinition('gunzipper')},
            SolidInvocation('snowflake_load'): {
                'start': DependencyDefinition('event_ingest', 'paths')
            },
        },
        mode_definitions=[
            ModeDefinition(resources={'s3': s3_resource, 'snowflake': snowflake_resource})
        ],
    )
