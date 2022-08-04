import os

from dagster import job, make_values_resource, op

# start_file_example




@op(required_resource_keys={"file_dirs"})
def write_file(context):
    filename = f"{context.resources.file_dirs['write_file_dir']}/new_file.txt"
    open(filename, "x").close()

    context.log.info(f"Created file: {filename}")


@op(required_resource_keys={"file_dirs"})
def total_num_files(context):
    files_in_dir = os.listdir(context.resources.file_dirs["count_file_dir"])
    context.log.info(f"Total number of files: {len(files_in_dir)}")


@job(
    resource_defs={
        "file_dirs": make_values_resource(write_file_dir=str, count_file_dir=str)
    }
)
def file_dirs_job():
    write_file()
    total_num_files()


# end_file_example
