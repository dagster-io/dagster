from dagster import Field, job, op


@op(config_schema={"asdf": Field(str, default_value="blah")})
def the_op():
    pass


@job
def the_job():
    the_op()
