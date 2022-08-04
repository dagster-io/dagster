import os

# start_file_example


from dagster import job, make_values_resource, op


@op(required_resource_keys={"file_dirs"})
def write_file(context):
    filename = f"{context.resources.file_dirs['write_file_dir']}/new_file.txt"
    open(filename, "x").close()

    context.log.info(f"Created file: {filename}")


@op(required_resource_keys={"file_dirs"})
def total_num_files(context):
    files_in_dir = os.listdir(context.resources.file_dirs['count_file_dir'])
    context.log.info(f"Total number of files: {len(files_in_dir)}")


@job(resource_defs={"file_dirs": make_values_resource(write_file_dir=str, count_file_dir=str)})
def file_dir_job():
    write_file()
    total_num_files()


result = file_dir_job.execute_in_process(
    run_config={
        "resources": {
            "file_dirs": {
                "config": {
                    "write_file_dir": "/write_files/",
                    "count_file_dir": "/count_files/",
                }
            }
        }
    }
)

# end_file_example
