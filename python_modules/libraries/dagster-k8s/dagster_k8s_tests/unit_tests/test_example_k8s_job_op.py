# isort: skip_file
# fmt: off
# start_marker
from dagster import job
from dagster_k8s import k8s_job_op

first_op = k8s_job_op.configured(
    {
        "image": "busybox",
        "command": ["/bin/sh", "-c"],
        "args": ["echo HELLO"],
    },
    name="first_op",
)
second_op = k8s_job_op.configured(
    {
        "image": "busybox",
        "command": ["/bin/sh", "-c"],
        "args": ["echo GOODBYE"],
    },
    name="second_op",
)

@job
def full_job():
    second_op(first_op())
# end_marker
# fmt: on


def test_k8s_job_op():
    assert full_job
