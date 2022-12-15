from dagster import Definitions, job, op


@op(required_resource_keys={"a_resource_key"})
def an_op():
    pass


@job
def a_job():
    an_op()


defs = Definitions(jobs=[a_job], resources={"a_resource_key": "some value"})

defs.get_job_def("a_job").execute_in_process()
