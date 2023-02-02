import os
from typing import Any, Dict

from dagster import job, make_values_resource, op
from dagster._config.structured_config import Resource

# start_file_example
from dagster._core.definitions.resource_output import Injected


class FileDirs(Resource):
    write_file_dir: str
    count_file_dir: str


@op
def write_file(context, file_dirs: FileDirs):
    filename = f"{file_dirs.write_file_dir}/new_file.txt"
    open(filename, "x", encoding="utf8").close()

    context.log.info(f"Created file: {filename}")


@op
def total_num_files(context, file_dirs: FileDirs):
    files_in_dir = os.listdir(file_dirs.count_file_dir)
    context.log.info(f"Total number of files: {len(files_in_dir)}")


@job(resource_defs={"file_dirs": FileDirs.configure_at_launch()})
def file_dirs_job():
    write_file()
    total_num_files()


# end_file_example
