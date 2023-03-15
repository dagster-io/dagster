# pylint: disable=unused-argument
from dagster import In, IOManager, Out, io_manager, job, op, root_input_manager


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


# start_marker
@root_input_manager(input_config_schema={"table_name": str})
def my_root_input_manager(context):
    return read_dataframe_from_table(name=context.config["table_name"])


class MyIOManager(IOManager):
    def handle_output(self, context, obj):
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context):
        return read_dataframe_from_table(name=context.upstream_output.name)


@io_manager
def my_io_manager(_):
    return MyIOManager()


@op(out=Out(io_manager_key="my_io_manager"))
def op1():
    """Do stuff."""


@op(ins={"dataframe": In(root_manager_key="my_root_input_manager")})
def op2(dataframe):
    """Do stuff."""


@job(
    resource_defs={
        "my_io_manager": my_io_manager,
        "my_root_input_manager": my_root_input_manager,
    }
)
def my_job():
    op2(op1())


# end_marker


def execute_full():
    my_job.execute_in_process()


def execute_subselection():
    # start_execute_subselection
    my_job.execute_in_process(
        run_config={
            "ops": {"op2": {"inputs": {"dataframe": {"table_name": "tableX"}}}}
        },
        op_selection=["op2"],
    )

    # end_execute_subselection
