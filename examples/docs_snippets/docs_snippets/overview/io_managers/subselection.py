# pylint: disable=unused-argument
from dagster import (
    Field,
    IOManager,
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    io_manager,
    pipeline,
    solid,
)


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


# start_marker
class MyIOManager(IOManager):
    def handle_output(self, context, obj):
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context):
        if "table_name" in context.config:
            table_name = context.config["table_name"]
        else:
            table_name = context.upstream_output.name

        return read_dataframe_from_table(name=table_name)


@io_manager(input_config_schema={"table_name": Field(str, is_required=False)})
def my_io_manager(_):
    return MyIOManager()


@solid(output_defs=[OutputDefinition(manager_key="my_io_manager")])
def solid1(_):
    """Do stuff"""


@solid(input_defs=[InputDefinition("dataframe", manager_key="my_io_manager")])
def solid2(_, dataframe):
    """Do stuff"""


@pipeline(mode_defs=[ModeDefinition(resource_defs={"my_io_manager": my_io_manager})])
def my_pipeline():
    solid2(solid1())


# end_marker


def execute_full():
    execute_pipeline(my_pipeline)


def execute_subselection():
    # start_execute_subselection
    execute_pipeline(
        my_pipeline,
        solid_selection=["solid2"],
        run_config={"solids": {"solid2": {"inputs": {"dataframe": {"table_name": "tableX"}}}}},
    )

    # end_execute_subselection
