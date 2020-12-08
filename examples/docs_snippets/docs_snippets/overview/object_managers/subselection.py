# pylint: disable=unused-argument
from dagster import (
    Field,
    InputDefinition,
    ModeDefinition,
    ObjectManager,
    OutputDefinition,
    execute_pipeline,
    object_manager,
    pipeline,
    solid,
)


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


# start_marker
class MyObjectManager(ObjectManager):
    def handle_output(self, context, obj):
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context):
        if "table_name" in context.input_config:
            table_name = context.input_config["table_name"]
        else:
            table_name = context.upstream_output.name

        return read_dataframe_from_table(name=table_name)


@object_manager(input_config_schema={"table_name": Field(str, is_required=False)})
def my_object_manager(_):
    return MyObjectManager()


@solid(output_defs=[OutputDefinition(manager_key="my_object_manager")])
def solid1(_):
    """Do stuff"""


@solid(input_defs=[InputDefinition("dataframe", manager_key="my_object_manager")])
def solid2(_, dataframe):
    """Do stuff"""


@pipeline(mode_defs=[ModeDefinition(resource_defs={"my_object_manager": my_object_manager})])
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
