from dagster import IOManager, Out, io_manager, job, op


def connect():
    pass


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


# ops_start_marker
@op(out=Out(metadata={"schema": "some_schema", "table": "some_table"}))
def op_1():
    """Return a Pandas DataFrame."""


@op(out=Out(metadata={"schema": "other_schema", "table": "other_table"}))
def op_2(_input_dataframe):
    """Return a Pandas DataFrame."""


# ops_end_marker


# io_manager_start_marker
class MyIOManager(IOManager):
    def handle_output(self, context, obj):
        table_name = context.metadata["table"]
        schema = context.metadata["schema"]
        write_dataframe_to_table(name=table_name, schema=schema, dataframe=obj)

    def load_input(self, context):
        table_name = context.upstream_output.metadata["table"]
        schema = context.upstream_output.metadata["schema"]
        return read_dataframe_from_table(name=table_name, schema=schema)


@io_manager
def my_io_manager(_):
    return MyIOManager()


# io_manager_end_marker


@job(resource_defs={"io_manager": my_io_manager})
def my_job():
    op_2(op_1())
