# ruff: isort: skip_file

# start_pipeline_marker

import dagster as dg


@dg.op
def return_one():
    return 1


@dg.op
def add_two(i: int):
    return i + 2


@dg.op
def multi_three(i: int):
    return i * 3


@dg.job
def my_job():
    multi_three(add_two(return_one()))


# end_pipeline_marker

# start_execute
if __name__ == "__main__":
    result = my_job.execute_in_process()

# end_execute


def execute_subset():
    # start_op_selection_marker
    my_job.execute_in_process(op_selection=["*add_two"])
    # end_op_selection_marker


@dg.op
def total(in_1: int, in_2: int, in_3: int, in_4: int):
    return in_1 + in_2 + in_3 + in_4


ip_yaml = """
# start_ip_yaml

execution:
  config:
    in_process:

# end_ip_yaml
"""


# start_mp_cfg
@dg.job(
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "start_method": {
                        "forkserver": {},
                    },
                    "max_concurrent": 4,
                },
            }
        }
    }
)
def forkserver_job():
    multi_three(add_two(return_one()))


# end_mp_cfg


# start_tag_concurrency
@dg.job(
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 4,
                    "tag_concurrency_limits": [
                        {
                            "key": "database",
                            "value": "redshift",
                            "limit": 2,
                        }
                    ],
                },
            }
        }
    }
)
def tag_concurrency_job(): ...


# end_tag_concurrency
