import os

import dagster as dg

if os.getenv("FOO") != "BAR":
    raise Exception("Missing env var")


@dg.op
def needs_env_var():
    if os.getenv("FOO_INSIDE_OP") != "BAR_INSIDE_OP":
        raise Exception("Missing env var inside op")


@dg.job
def needs_env_var_job():
    needs_env_var()


@dg.repository
def needs_env_var_repo():
    return [needs_env_var_job]
