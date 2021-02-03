import pytest
from dagster import (
    DagsterInvalidConfigError,
    Field,
    String,
    composite_solid,
    execute_pipeline,
    pipeline,
    solid,
)


def test_basic_solid_with_config():
    did_get = {}

    @solid(
        name="solid_with_context",
        input_defs=[],
        output_defs=[],
        config_schema={"some_config": Field(String)},
    )
    def solid_with_context(context):
        did_get["yep"] = context.solid_config

    @pipeline
    def pipeline_def():
        solid_with_context()

    execute_pipeline(
        pipeline_def, {"solids": {"solid_with_context": {"config": {"some_config": "foo"}}}}
    )

    assert "yep" in did_get
    assert "some_config" in did_get["yep"]


def test_config_arg_mismatch():
    def _t_fn(*_args):
        raise Exception("should not reach")

    @solid(
        name="solid_with_context",
        input_defs=[],
        output_defs=[],
        config_schema={"some_config": Field(String)},
    )
    def solid_with_context(context):
        raise Exception("should not reach")

    @pipeline
    def pipeline_def():
        solid_with_context()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            pipeline_def, {"solids": {"solid_with_context": {"config": {"some_config": 1}}}}
        )


def test_solid_not_found():
    @solid(name="find_me_solid", input_defs=[], output_defs=[])
    def find_me_solid(_):
        raise Exception("should not reach")

    @pipeline
    def pipeline_def():
        find_me_solid()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(pipeline_def, {"solids": {"not_found": {"config": {"some_config": 1}}}})


def test_config_for_no_config():
    @solid(name="no_config_solid", input_defs=[], output_defs=[])
    def no_config_solid(_):
        raise Exception("should not reach")

    @pipeline
    def pipeline_def():
        return no_config_solid()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            pipeline_def, {"solids": {"no_config_solid": {"config": {"some_config": 1}}}}
        )


def test_extra_config_ignored_default_input():
    @solid(config_schema={"some_config": str})
    def solid1(_):
        return "public.table_1"

    @solid
    def solid2(_, input_table="public.table_1"):
        return input_table

    @pipeline
    def my_pipeline():
        solid2(solid1())

    run_config = {"solids": {"solid1": {"config": {"some_config": "a"}}}}
    assert execute_pipeline(my_pipeline, run_config=run_config).success

    # same run config is valid even though solid1 not in subset
    assert execute_pipeline(my_pipeline, run_config=run_config, solid_selection=["solid2"]).success

    with pytest.raises(DagsterInvalidConfigError):
        # typos still raise, solid_1 instead of solid1
        execute_pipeline(
            my_pipeline,
            {"solids": {"solid_1": {"config": {"some_config": "a"}}}},
            solid_selection=["solid2"],
        )


def test_extra_config_ignored_no_default_input():
    @solid(config_schema={"some_config": str})
    def solid1(_):
        return "public.table_1"

    @solid
    def solid2(_, input_table):
        return input_table

    @pipeline
    def my_pipeline():
        solid2(solid1())

    run_config = {"solids": {"solid1": {"config": {"some_config": "a"}}}}
    assert execute_pipeline(my_pipeline, run_config=run_config).success

    # run config is invalid since there is no input for solid2
    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            my_pipeline,
            run_config=run_config,
            solid_selection=["solid2"],
        )

    # works if input added, don't need to remove other stuff
    run_config["solids"]["solid2"] = {"inputs": {"input_table": {"value": "public.table_1"}}}
    assert execute_pipeline(
        my_pipeline,
        run_config=run_config,
        solid_selection=["solid2"],
    ).success

    # input for solid2 ignored if select solid1
    assert execute_pipeline(
        my_pipeline,
        run_config=run_config,
        solid_selection=["solid1"],
    ).success


def test_extra_config_ignored_composites():
    @solid(config_schema={"some_config": str})
    def solid1(_):
        return "public.table_1"

    @composite_solid(
        config_schema={"wrapped_config": str},
        config_fn=lambda cfg: {"solid1": {"config": {"some_config": cfg["wrapped_config"]}}},
    )
    def composite1():
        return solid1()

    @solid
    def solid2(_, input_table="public.table"):
        return input_table

    @composite_solid
    def composite2(input_table):
        return solid2(input_table)

    @pipeline
    def my_pipeline():
        composite2(composite1())

    run_config = {"solids": {"composite1": {"config": {"wrapped_config": "a"}}}}
    assert execute_pipeline(my_pipeline, run_config=run_config).success

    assert execute_pipeline(
        my_pipeline, run_config=run_config, solid_selection=["composite2"]
    ).success

    assert execute_pipeline(
        my_pipeline, run_config=run_config, solid_selection=["composite1"]
    ).success
