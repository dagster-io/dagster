from dagster import Backoff, Jitter, RetryPolicy, RetryRequested, job, op


def fails_sometimes():
    raise Exception("jk, its always")


def should_retry(_):
    return True


# problem_start
@op
def problematic():
    fails_sometimes()


# problem_end

# policy_start
@op(retry_policy=RetryPolicy())
def better():
    fails_sometimes()


# policy_end

# policy2_start
@op(
    retry_policy=RetryPolicy(
        max_retries=3,
        delay=0.2,  # 200ms
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.PLUS_MINUS,
    )
)
def even_better():
    fails_sometimes()


# policy2_end


# manual_start
@op
def manual():
    try:
        fails_sometimes()
    except Exception as e:
        if should_retry(e):
            raise RetryRequested(max_retries=1, seconds_to_wait=1) from e
        else:
            raise


# manual_end


@job
def retry_job():
    problematic()
    better()
    even_better()
    manual()
