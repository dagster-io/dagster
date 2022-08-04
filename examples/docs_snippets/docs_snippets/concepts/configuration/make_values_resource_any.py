import os

from dagster import job, make_values_resource, op

# start_file_example




@op(required_resource_keys={"file_dir"})
def add_file(context):
    filename = f"{context.resources.file_dir}/new_file.txt"
    open(filename, "x").close()

    context.log.info(f"Created file: {filename}")


@op(required_resource_keys={"file_dir"})
def total_num_files(context):
    files_in_dir = os.listdir(context.resources.file_dir)
    context.log.info(f"Total number of files: {len(files_in_dir)}")


@job(resource_defs={"file_dir": make_values_resource()})
def file_dir_job():
    add_file()
    total_num_files()


# end_file_example
