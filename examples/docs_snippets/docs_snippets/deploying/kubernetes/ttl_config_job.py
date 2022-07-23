# pylint: disable=print-call
from dagster import job, op


@op
def my_op():
    print("foo")  # pylint: disable=print-call


# fmt: off
# start_ttl
@job(
    tags = {
        'dagster-k8s/config': {
            'job_spec_config': {
                'ttl_seconds_after_finished': 7200
            }
        }
    }
)
def my_job():
    my_op()
# end_ttl
# fmt: on
