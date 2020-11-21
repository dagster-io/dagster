import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    InputDefinition,
    Int,
    Output,
    OutputDefinition,
    PipelineDefinition,
    composite_solid,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
    usable_as_dagster_type,
)


def builder(graph):
    return graph.add_one(graph.return_one())


@lambda_solid
def return_one():
    return 1


@lambda_solid
def return_two():
    return 2


@lambda_solid
def return_three():
    return 3


@lambda_solid(input_defs=[InputDefinition("num")])
def add_one(num):
    return num + 1


def test_basic_use_case():
    pipeline_def = PipelineDefinition(
        name="basic",
        solid_defs=[return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )

    assert execute_pipeline(pipeline_def).result_for_solid("add_one").output_value() == 2


def test_basic_use_case_with_dsl():
    @pipeline
    def test():
        add_one(num=return_one())

    assert execute_pipeline(test).result_for_solid("add_one").output_value() == 2


def test_two_inputs_without_dsl():
    @lambda_solid(input_defs=[InputDefinition("num_one"), InputDefinition("num_two")])
    def subtract(num_one, num_two):
        return num_one - num_two

    pipeline_def = PipelineDefinition(
        solid_defs=[subtract, return_two, return_three],
        dependencies={
            "subtract": {
                "num_one": DependencyDefinition("return_two"),
                "num_two": DependencyDefinition("return_three"),
            }
        },
    )

    assert execute_pipeline(pipeline_def).result_for_solid("subtract").output_value() == -1


def test_two_inputs_with_dsl():
    @lambda_solid(input_defs=[InputDefinition("num_one"), InputDefinition("num_two")])
    def subtract(num_one, num_two):
        return num_one - num_two

    @pipeline
    def test():
        subtract(num_one=return_two(), num_two=return_three())

    assert execute_pipeline(test).result_for_solid("subtract").output_value() == -1


def test_basic_aliasing_with_dsl():
    @pipeline
    def test():
        add_one.alias("renamed")(num=return_one())

    assert execute_pipeline(test).result_for_solid("renamed").output_value() == 2


def test_diamond_graph():
    @solid(output_defs=[OutputDefinition(name="value_one"), OutputDefinition(name="value_two")])
    def emit_values(_context):
        yield Output(1, "value_one")
        yield Output(2, "value_two")

    @lambda_solid(input_defs=[InputDefinition("num_one"), InputDefinition("num_two")])
    def subtract(num_one, num_two):
        return num_one - num_two

    @pipeline
    def diamond_pipeline():
        value_one, value_two = emit_values()
        subtract(num_one=add_one(num=value_one), num_two=add_one.alias("renamed")(num=value_two))

    result = execute_pipeline(diamond_pipeline)

    assert result.result_for_solid("subtract").output_value() == -1


def test_two_cliques():
    @pipeline
    def diamond_pipeline():
        return_one()
        return_two()

    result = execute_pipeline(diamond_pipeline)

    assert result.result_for_solid("return_one").output_value() == 1
    assert result.result_for_solid("return_two").output_value() == 2


def test_deep_graph():
    @solid(config_schema=Int)
    def download_num(context):
        return context.solid_config

    @lambda_solid(input_defs=[InputDefinition("num")])
    def unzip_num(num):
        return num

    @lambda_solid(input_defs=[InputDefinition("num")])
    def ingest_num(num):
        return num

    @lambda_solid(input_defs=[InputDefinition("num")])
    def subsample_num(num):
        return num

    @lambda_solid(input_defs=[InputDefinition("num")])
    def canonicalize_num(num):
        return num

    @lambda_solid(input_defs=[InputDefinition("num")])
    def load_num(num):
        return num + 3

    @pipeline
    def test():
        load_num(
            num=canonicalize_num(
                num=subsample_num(num=ingest_num(num=unzip_num(num=download_num())))
            )
        )

    result = execute_pipeline(test, {"solids": {"download_num": {"config": 123}}})
    assert result.result_for_solid("canonicalize_num").output_value() == 123
    assert result.result_for_solid("load_num").output_value() == 126


def test_unconfigurable_inputs_pipeline():
    @usable_as_dagster_type
    class NewType:
        pass

    @lambda_solid(input_defs=[InputDefinition("_", NewType)])
    def noop(_):
        pass

    with pytest.raises(DagsterInvalidDefinitionError):
        # NewType is not connect and can not be provided with config
        @pipeline
        def _bad_inputs():
            noop()


def test_dupe_defs_fail():
    @lambda_solid(name="same")
    def noop():
        pass

    @lambda_solid(name="same")
    def noop2():
        pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @pipeline
        def _dupes():
            noop()
            noop2()

    with pytest.raises(DagsterInvalidDefinitionError):
        PipelineDefinition(name="dupes", solid_defs=[noop, noop2])


def test_composite_dupe_defs_fail():
    @lambda_solid
    def noop():
        pass

    @composite_solid(name="same")
    def composite_noop():
        noop()
        noop()
        noop()

    @composite_solid(name="same")
    def composite_noop2():
        noop()

    @composite_solid
    def wrapper():
        composite_noop2()

    @composite_solid
    def top():
        wrapper()
        composite_noop()

    with pytest.raises(DagsterInvalidDefinitionError):

        @pipeline
        def _dupes():
            composite_noop()
            composite_noop2()

    with pytest.raises(DagsterInvalidDefinitionError):
        PipelineDefinition(name="dupes", solid_defs=[top])


def test_two_inputs_with_reversed_input_defs_and_dsl():
    @solid(input_defs=[InputDefinition("num_two"), InputDefinition("num_one")])
    def subtract_ctx(_context, num_one, num_two):
        return num_one - num_two

    @lambda_solid(input_defs=[InputDefinition("num_two"), InputDefinition("num_one")])
    def subtract(num_one, num_two):
        return num_one - num_two

    @pipeline
    def test():
        two = return_two()
        three = return_three()
        subtract(two, three)
        subtract_ctx(two, three)

    assert execute_pipeline(test).result_for_solid("subtract").output_value() == -1
    assert execute_pipeline(test).result_for_solid("subtract_ctx").output_value() == -1


def test_single_non_positional_input_use():
    @lambda_solid(input_defs=[InputDefinition("num")])
    def add_one_kw(**kwargs):
        return kwargs["num"] + 1

    @pipeline
    def test():
        # the decorated solid fn doesn't define args
        # but since there is only one it is unambiguous
        add_one_kw(return_two())

    assert execute_pipeline(test).result_for_solid("add_one_kw").output_value() == 3


def test_single_positional_single_kwarg_input_use():
    @lambda_solid(input_defs=[InputDefinition("num_two"), InputDefinition("num_one")])
    def subtract_kw(num_one, **kwargs):
        return num_one - kwargs["num_two"]

    @pipeline
    def test():
        # the decorated solid fn only defines one positional arg
        # and one kwarg so passing two by position is unambiguous
        # since the second argument must be the one kwarg
        subtract_kw(return_two(), return_three())

    assert execute_pipeline(test).result_for_solid("subtract_kw").output_value() == -1


def test_bad_positional_input_use():
    @lambda_solid(
        input_defs=[
            InputDefinition("num_two"),
            InputDefinition("num_one"),
            InputDefinition("num_three"),
        ]
    )
    def add_kw(num_one, **kwargs):
        return num_one + kwargs["num_two"] + kwargs["num_three"]

    with pytest.raises(DagsterInvalidDefinitionError, match="Use keyword args instead"):

        @pipeline
        def _fail():
            # the decorated solid fn only defines one positional arg
            # so the two remaining have no positions and this is
            # ambiguous
            add_kw(return_two(), return_two(), return_two())


def test_nameless():
    noname = PipelineDefinition([return_one])

    assert noname.name.startswith("__pipeline")
    assert noname.display_name.startswith("__pipeline")
