from dagster import (
    AssetMaterialization,
    ExpectationResult,
    InputDefinition,
    Output,
    OutputDefinition,
    pipeline,
    repository,
    solid,
)


# start_repo_marker_0
@solid
def add_one(_, num: int) -> int:
    return num + 1


@solid
def add_two(_, num: int) -> int:
    return num + 2


@solid
def subtract(_, left: int, right: int) -> int:
    return left - right


@pipeline
def do_math():
    subtract(add_one(), add_two())


@solid(
    input_defs=[InputDefinition(name="input_num", dagster_type=int)],
    # with multiple outputs, you must specify your outputs via
    # OutputDefinitions, rather than type annotations
    output_defs=[
        OutputDefinition(name="a_num", dagster_type=int),
        OutputDefinition(name="a_string", dagster_type=str),
    ],
)
def emit_events_solid(_, input_num):
    a_num = input_num + 1
    a_string = "foo"
    yield ExpectationResult(
        success=a_num > 0, label="positive", description="A num must be positive"
    )
    yield AssetMaterialization(
        asset_key="persisted_string", description="Let us pretend we persisted the string somewhere"
    )
    yield Output(value=a_num, output_name="a_num")
    yield Output(value=a_string, output_name="a_string")


@pipeline
def emit_events_pipeline():
    emit_events_solid()


# end_repo_marker_0


@repository
def pipeline_unittesting():
    return [do_math, emit_events_pipeline]
