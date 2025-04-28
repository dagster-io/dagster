from dagster import ConfigurableIOManager, InputContext, Out, OutputContext, job, op


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
class MyIOManager(ConfigurableIOManager):
    def handle_output(self, context: OutputContext, obj):
        if context.definition_metadata:
            table_name = context.definition_metadata["table"]
            schema = context.definition_metadata["schema"]
            write_dataframe_to_table(name=table_name, schema=schema, dataframe=obj)
        else:
            raise Exception(
                f"op {context.op_def.name} doesn't have schema and metadata set"
            )

    def load_input(self, context: InputContext):
        if context.upstream_output and context.upstream_output.definition_metadata:
            table_name = context.upstream_output.definition_metadata["table"]
            schema = context.upstream_output.definition_metadata["schema"]
            return read_dataframe_from_table(name=table_name, schema=schema)
        else:
            raise Exception("Upstream output doesn't have schema and metadata set")


# io_manager_end_marker


@job(resource_defs={"io_manager": MyIOManager()})
def my_job():
    op_2(op_1())
