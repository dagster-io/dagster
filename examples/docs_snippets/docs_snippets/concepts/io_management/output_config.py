from dagster import IOManager, io_manager, job, op


def connect():
    pass


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


@op
def op_1():
    """Return a Pandas DataFrame."""


@op
def op_2(_input_dataframe):
    """Return a Pandas DataFrame."""


# io_manager_start_marker
class MyIOManager(IOManager):
    def handle_output(self, context, obj):
        table_name = context.config["table"]
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context):
        table_name = context.upstream_output.config["table"]
        return read_dataframe_from_table(name=table_name)


@io_manager(output_config_schema={"table": str})
def my_io_manager(_):
    return MyIOManager()


# io_manager_end_marker


# execute_start_marker
def execute_my_job_with_config():
    @job(resource_defs={"io_manager": my_io_manager})
    def my_job():
        op_2(op_1())

    my_job.execute_in_process(
        run_config={
            "ops": {
                "op_1": {"outputs": {"result": {"table": "table1"}}},
                "op_2": {"outputs": {"result": {"table": "table2"}}},
            }
        },
    )


# execute_end_marker
