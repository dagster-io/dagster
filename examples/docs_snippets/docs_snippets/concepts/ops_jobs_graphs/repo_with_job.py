from dagster import Definitions, job


@job
def do_it_all(): ...


defs = Definitions(jobs=[do_it_all])
