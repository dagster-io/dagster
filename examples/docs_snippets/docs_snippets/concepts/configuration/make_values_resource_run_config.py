from .make_values_resource_any import file_dir_job
from .make_values_resource_config_schema import file_dirs_job

# start_run_config_1

result = file_dir_job.execute_in_process(
    run_config={"resources": {"file_dir": {"config": "/my_files/"}}}
)

# end_run_config_1

# start_run_config_2

result = file_dirs_job.execute_in_process(
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

# end_run_config_2
