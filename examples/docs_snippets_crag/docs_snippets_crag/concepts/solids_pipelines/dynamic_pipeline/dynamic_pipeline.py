# pylint: disable=unused-argument, no-value-for-parameter

# start_marker
import os
from typing import List

from dagster import DynamicOutput, DynamicOutputDefinition, Field, pipeline, solid
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
def process_file(path: str) -> int:
    # simple example of calculating size
    return os.path.getsize(path)


@solid
def summarize_directory(sizes: List[int]) -> int:
    # simple example of totalling sizes
    return sum(sizes)


@pipeline
def process_directory():
    file_results = files_in_directory().map(process_file)
    summarize_directory(file_results.collect())


# end_marker
