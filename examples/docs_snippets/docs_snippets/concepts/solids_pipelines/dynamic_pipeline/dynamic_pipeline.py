# pylint: disable=unused-argument, no-value-for-parameter

# start_marker
import os

from dagster import Field, pipeline, solid
from dagster.experimental import DynamicOutput, DynamicOutputDefinition
from dagster.utils import file_relative_path


@solid(
    config_schema={"path": Field(str, default_value=file_relative_path(__file__, "sample"))},
    output_defs=[DynamicOutputDefinition(str)],
)
def files_in_directory(context):
    path = context.solid_config["path"]
    dirname, _, filenames = next(os.walk(path))
    for file in filenames:
        yield DynamicOutput(
            value=os.path.join(dirname, file),
            # create a mapping key from the file name
            mapping_key=file.replace(".", "_").replace("-", "_"),
        )


@solid
def process_file(_, path: str) -> int:
    # simple example of calculating size
    return os.path.getsize(path)


@pipeline
def process_directory():
    files_in_directory().map(process_file)


# end_marker
