import dagster as dg


def fails_sometimes():
    raise Exception("jk, its always")


def should_retry(_):
    return True


# problem_start
@dg.op
def problematic():
    fails_sometimes()


# problem_end


# policy_start
@dg.op(retry_policy=dg.RetryPolicy())
def better():
    fails_sometimes()


# policy_end


# policy2_start
@dg.op(
    retry_policy=dg.RetryPolicy(
        max_retries=3,
        delay=0.2,  # 200ms
        backoff=dg.Backoff.EXPONENTIAL,
        jitter=dg.Jitter.PLUS_MINUS,
    )
)
def even_better():
    fails_sometimes()


# policy2_end

# policy3_start
default_policy = dg.RetryPolicy(max_retries=1)
flakey_op_policy = dg.RetryPolicy(max_retries=10)


@dg.job(op_retry_policy=default_policy)
def default_and_override_job():
    problematic.with_retry_policy(flakey_op_policy)()


# policy3_end


# manual_start
@dg.op
def manual():
    try:
        fails_sometimes()
    except Exception as e:
        if should_retry(e):
            raise dg.RetryRequested(max_retries=1, seconds_to_wait=1) from e
        else:
            raise


# manual_end


@dg.job
def retry_job():
    problematic()
    better()
    even_better()
    manual()
