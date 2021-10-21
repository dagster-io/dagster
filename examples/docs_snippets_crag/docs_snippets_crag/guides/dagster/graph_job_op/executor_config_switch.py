from dagster import job


# This job will run with multiprocessing execution
@job
def do_it_all():
    ...


# This job will run with in-process execution
@job(config={"execution": {"config": {"in_process": {}}}})
def do_it_all_in_proc():
    ...
