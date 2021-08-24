# pylint: disable=unused-argument
from dagster import (
    IOManager,
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    io_manager,
    pipeline,
    root_input_manager,
    solid,
)


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


@solid(output_defs=[OutputDefinition(io_manager_key="my_io_manager")])
def solid1():
    """Do stuff"""


@solid(input_defs=[InputDefinition("dataframe", root_manager_key="my_root_input_manager")])
def solid2(dataframe):
    """Do stuff"""


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "my_io_manager": my_io_manager,
                "my_root_input_manager": my_root_input_manager,
            }
        )
    ]
)
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
