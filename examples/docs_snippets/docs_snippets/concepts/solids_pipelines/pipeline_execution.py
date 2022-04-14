# isort: skip_file

# start_pipeline_marker

from dagster import job, op


@op
def return_one():
    return 1


@op
def add_two(i: int):
    return i + 2


@op
def multi_three(i: int):
    return i * 3


@job
def my_job():
    multi_three(add_two(return_one()))


# end_pipeline_marker

# start_execute_marker
if __name__ == "__main__":
    result = my_job.execute_in_process()

# end_execute_marker


def execute_subset():
    # start_solid_selection_marker
    my_job.execute_in_process(op_selection=["*add_two"])
    # end_solid_selection_marker


@op
def total(in_1: int, in_2: int, in_3: int, in_4: int):
    return in_1 + in_2 + in_3 + in_4
