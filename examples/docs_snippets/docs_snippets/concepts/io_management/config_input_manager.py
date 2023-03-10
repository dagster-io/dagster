# pylint: disable=unused-argument
from dagster import In, job, op, root_input_manager


def read_dataframe_from_table(**_kwargs):
    pass


@op(ins={"dataframe": In(root_manager_key="my_root_manager")})
def my_op(dataframe):
    """Do some stuff."""


# def_start_marker
@root_input_manager(input_config_schema={"table_name": str})
def table_loader(context):
    return read_dataframe_from_table(name=context.config["table_name"])


# def_end_marker


def execute_with_config():
    # execute_start_marker
    @job(resource_defs={"my_root_manager": table_loader})
    def my_job():
        my_op()

    my_job.execute_in_process(
        run_config={
            "ops": {"my_op": {"inputs": {"dataframe": {"table_name": "table1"}}}}
        },
    )
    # execute_end_marker
