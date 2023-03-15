# pylint: disable=unused-argument
from dagster import In, job, op, root_input_manager


def read_dataframe_from_table(**_kwargs):
    pass


# start_marker
@op(ins={"dataframe": In(root_manager_key="my_root_manager")})
def my_op(dataframe):
    """Do some stuff."""


@root_input_manager
def table1_loader(_):
    return read_dataframe_from_table(name="table1")


@job(resource_defs={"my_root_manager": table1_loader})
def my_job():
    my_op()


# end_marker
