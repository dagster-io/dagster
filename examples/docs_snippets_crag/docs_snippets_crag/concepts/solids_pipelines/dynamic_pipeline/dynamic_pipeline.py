# pylint: disable=unused-argument, no-value-for-parameter, no-member

# start_marker
import os
from typing import List

from dagster import DynamicOut, DynamicOutput, Field, graph, op
from dagster.utils import file_relative_path


@op(
    config_schema={"path": Field(str, default_value=file_relative_path(__file__, "sample"))},
    out=DynamicOut(str),
)
def files_in_directory(context):
    path = context.op_config["path"]
    dirname, _, filenames = next(os.walk(path))
    for file in filenames:
        yield DynamicOutput(
            value=os.path.join(dirname, file),
            # create a mapping key from the file name
            mapping_key=file.replace(".", "_").replace("-", "_"),
        )


@op
def process_file(path: str) -> int:
    # simple example of calculating size
    return os.path.getsize(path)


@op
def summarize_directory(sizes: List[int]) -> int:
    # simple example of totalling sizes
    return sum(sizes)


@graph
def process_directory():
    file_results = files_in_directory().map(process_file)
    summarize_directory(file_results.collect())


# end_marker
