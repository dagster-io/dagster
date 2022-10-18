import os

from dagster import job, op, repository

if os.getenv("FOO") != "BAR":
    raise Exception("Missing env var")


@op
def needs_env_var():
    pass


@job
def needs_env_var_job():
    needs_env_var()


@repository
def needs_env_var_repo():
    return [needs_env_var_job]
