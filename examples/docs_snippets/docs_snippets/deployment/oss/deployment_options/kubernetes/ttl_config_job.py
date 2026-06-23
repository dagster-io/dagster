# ruff: noqa: T201
import dagster as dg


@dg.op
def my_op():
    print("foo")


# fmt: off
# start_ttl
@dg.job(
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
