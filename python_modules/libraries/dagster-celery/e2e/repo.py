import time

from dagster import job, op, repository


@op
def sleepy_op(context):
    """Op that sleeps for a long time — useful for testing crash detection."""
    context.log.info("Starting sleepy_op, will sleep for 300 seconds...")
    for i in range(300):
        time.sleep(1)
        if i % 30 == 0:
            context.log.info(f"Still sleeping... {i}/300 seconds")


@op
def noop_op():
    pass


@job
def sleepy_job():
    sleepy_op()


@job
def noop_job():
    noop_op()


@repository
def e2e_test_repository():
    return [sleepy_job, noop_job]
