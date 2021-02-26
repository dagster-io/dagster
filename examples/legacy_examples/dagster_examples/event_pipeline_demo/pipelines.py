"""Pipeline definitions for the airline_demo."""

import gzip
import os
import shutil

from dagster import (
    Bool,
    DagsterType,
    Field,
    InputDefinition,
    List,
    ModeDefinition,
    Nothing,
    OutputDefinition,
    PresetDefinition,
    String,
    TypeCheck,
    pipeline,
    solid,
)
from dagster.utils import mkdir_p, safe_isfile
from dagster_aws.s3 import S3Callback, s3_resource
from dagster_snowflake import snowflake_resource
from dagster_spark import create_spark_solid, spark_resource


def file_exists_at_path_type_check(_, value):
    if not isinstance(value, str):
        return TypeCheck(
            success=False,
            description="FileExistsAtPath must be a string in memory. Got {value}".format(
                value=repr(value)
            ),
        )
    if not safe_isfile(value):
        return TypeCheck(
            success=False,
            description=(
                "FileExistsAtPath must be a path that points to a file that "
                'exists. "{value}" does not exist on disk'
            ).format(value=value),
        )

    return True


FileExistsAtPath = DagsterType(
    name="FileExistsAtPath",
    description="A path at which a file actually exists",
    type_check_fn=file_exists_at_path_type_check,
)


def _download_from_s3_to_file(session, context, bucket, key, target_folder, skip_if_present):
    # TODO: remove context argument once we support resource logging

    # file name is S3 key path suffix after last /
    target_file = os.path.join(target_folder, key.split("/")[-1])

    if skip_if_present and safe_isfile(target_file):
        context.log.info(
            "Skipping download, file already present at {target_file}".format(
                target_file=target_file
            )
        )
    else:
        if not os.path.exists(target_folder):
            mkdir_p(target_folder)

        context.log.info(
            "Starting download of {bucket}/{key} to {target_file}".format(
                bucket=bucket, key=key, target_file=target_file
            )
        )

        headers = session.head_object(Bucket=bucket, Key=key)
        callback = S3Callback(
            context.log.debug, bucket, key, target_file, int(headers["ContentLength"])
        )
        session.download_file(Bucket=bucket, Key=key, Filename=target_file, Callback=callback)
    return target_file


# This should be ported to use FileHandle-based solids.
# See https://github.com/dagster-io/dagster/issues/1476
@solid(
    name="download_from_s3_to_file",
    config_schema={
        "bucket": Field(String, description="S3 bucket name"),
        "key": Field(String, description="S3 key name"),
        "target_folder": Field(
            String, description=("Specifies the path at which to download the object.")
        ),
        "skip_if_present": Field(Bool, is_required=False, default_value=False),
    },
    description="Downloads an object from S3 to a file.",
    output_defs=[
        OutputDefinition(FileExistsAtPath, description="The path to the downloaded object.")
    ],
    required_resource_keys={"s3"},
)
def download_from_s3_to_file(context):
    """Download an object from S3 to a local file."""
    (bucket, key, target_folder, skip_if_present) = (
        context.solid_config.get(k) for k in ("bucket", "key", "target_folder", "skip_if_present")
    )

    return _download_from_s3_to_file(
        context.resources.s3, context, bucket, key, target_folder, skip_if_present
    )


@solid(
    input_defs=[InputDefinition("gzip_file", String)], output_defs=[OutputDefinition(List[String])]
)
def gunzipper(_, gzip_file):
    """gunzips /path/to/foo.gz to /path/to/raw/2019/01/01/data.json"""
    # TODO: take date as an input

    path_prefix = os.path.dirname(gzip_file)
    output_folder = os.path.join(path_prefix, "raw/2019/01/01")
    outfile = os.path.join(output_folder, "data.json")

    if not safe_isfile(outfile):
        mkdir_p(output_folder)

        with gzip.open(gzip_file, "rb") as f_in, open(outfile, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    return [path_prefix]


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="default",
            resource_defs={
                "s3": s3_resource,
                "snowflake": snowflake_resource,
                "spark": spark_resource,
            },
        )
    ],
    preset_defs=[
        PresetDefinition.from_pkg_resources(
            "default",
            pkg_resource_defs=[
                ("dagster_examples.event_pipeline_demo.environments", "default.yaml"),
            ],
        )
    ],
)
def event_ingest_pipeline():
    event_ingest = create_spark_solid(
        name="event_ingest",
        main_class="io.dagster.events.EventPipeline",
        description="Ingest events from JSON to Parquet",
    )

    @solid(input_defs=[InputDefinition("start", Nothing)], required_resource_keys={"snowflake"})
    def snowflake_load(context):
        # TODO: express dependency of this solid on event_ingest
        context.resources.snowflake.load_table_from_local_parquet(
            src="file:///tmp/dagster/events/data/output/2019/01/01/*.parquet", table="events"
        )

    snowflake_load(event_ingest(start=gunzipper(gzip_file=download_from_s3_to_file())))
