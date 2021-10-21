from dagster import job, multiprocess_executor


@job(executor_def=multiprocess_executor, config={"execution": {"config": {"max_concurrent": 5}}})
def do_it_all():
    ...
