from dagster import (
    EventMetadataEntry,
    PresetDefinition,
    String,
    TypeCheck,
    dagster_type,
    input_hydration_config,
    lambda_solid,
    output_materialization_config,
    pipeline,
    solid,
)
from dagster.utils import script_relative_path

# pylint: disable=no-value-for-parameter


@dagster_type
class Empty:
    pass


@input_hydration_config(String)
def read_sauce(_context, path):
    with open(script_relative_path(path), 'r') as fd:
        return Sauce(fd.read())


@output_materialization_config(String)
def write_sauce(_context, path, sauce):
    with open(path, 'w+') as fd:
        fd.write(sauce.flavor)


@dagster_type(
    input_hydration_config=read_sauce,  # how to create an instance from config
    output_materialization_config=write_sauce,  # how to materialize an instance
    typecheck_metadata_fn=lambda sauce: TypeCheck(
        metadata_entries=[
            EventMetadataEntry.text(
                label='is_spicy', text='yes' if 'spicy' in sauce.flavor else 'no'
            )
        ]
    ),
)
class Sauce:
    def __init__(self, flavor='tangy'):
        self.flavor = flavor


@lambda_solid
def make_burger():
    return 'cheese burger'


@lambda_solid
def add_sauce(food, sauce: Sauce):
    return '{food} with {flavor} sauce'.format(food=food, flavor=sauce.flavor)


@solid
def inspect_sauce(context, sauce: Sauce) -> Sauce:
    context.log.info('The sauce tastes {flavor}'.format(flavor=sauce.flavor))
    return sauce


@pipeline(
    preset_defs=[
        PresetDefinition.from_files('test', [script_relative_path('./custom_type_input.yaml')])
    ]
)
def burger_time():
    inspected_sauce = inspect_sauce()
    add_sauce(make_burger(), inspected_sauce)
