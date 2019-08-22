import os

from dagster import check, seven


def base_runs_directory():
    return os.path.join(seven.get_system_temp_directory(), 'dagster', 'runs')


def base_directory_for_run(run_id):
    check.str_param(run_id, 'run_id')
    return os.path.join(base_runs_directory(), run_id)


def meta_file(base_dir):
    return os.path.join(base_dir, 'runmeta.jsonl')
