import pytest

from dagster import DagsterInvalidConfigError, Field, In, String, op, root_input_manager
from dagster._legacy import ModeDefinition, composite_solid, execute_pipeline, pipeline


def test_basic_solid_with_config():
    did_get = {}

    @op(
        name="op_with_context",
        ins={},
        out={},
        config_schema={"some_config": Field(String)},
    )
    def op_with_context(context):
        did_get["yep"] = context.op_config

    @pipeline
    def pipeline_def():
        op_with_context()

    execute_pipeline(
        pipeline_def,
        {"solids": {"op_with_context": {"config": {"some_config": "foo"}}}},
    )

    assert "yep" in did_get
    assert "some_config" in did_get["yep"]


def test_config_arg_mismatch():
    def _t_fn(*_args):
        raise Exception("should not reach")

    @op(
        name="op_with_context",
        ins={},
        out={},
        config_schema={"some_config": Field(String)},
    )
    def op_with_context(context):
        raise Exception("should not reach")

    @pipeline
    def pipeline_def():
        op_with_context()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            pipeline_def,
            {"solids": {"op_with_context": {"config": {"some_config": 1}}}},
        )


def test_solid_not_found():
    @op(name="find_me_op", ins={}, out={})
    def find_me_op(_):
        raise Exception("should not reach")

    @pipeline
    def pipeline_def():
        find_me_op()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(pipeline_def, {"solids": {"not_found": {"config": {"some_config": 1}}}})


def test_extra_config_ignored_default_input():
    @op(config_schema={"some_config": str})
    def op1(_):
        return "public.table_1"

    @op
    def op2(_, input_table="public.table_1"):
        return input_table

    @pipeline
    def my_pipeline():
        op2(op1())

    run_config = {"solids": {"op1": {"config": {"some_config": "a"}}}}
    assert execute_pipeline(my_pipeline, run_config=run_config).success

    # same run config is valid even though solid1 not in subset
    assert execute_pipeline(my_pipeline, run_config=run_config, solid_selection=["op2"]).success

    with pytest.raises(DagsterInvalidConfigError):
        # typos still raise, solid_1 instead of solid1
        execute_pipeline(
            my_pipeline,
            {"solids": {"solid_1": {"config": {"some_config": "a"}}}},
            solid_selection=["op2"],
        )


def test_extra_config_ignored_no_default_input():
    @op(config_schema={"some_config": str})
    def op1(_):
        return "public.table_1"

    @op
    def op2(_, input_table):
        return input_table

    @pipeline
    def my_pipeline():
        op2(op1())

    run_config = {"solids": {"op1": {"config": {"some_config": "a"}}}}
    assert execute_pipeline(my_pipeline, run_config=run_config).success

    # run config is invalid since there is no input for solid2
    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            my_pipeline,
            run_config=run_config,
            solid_selection=["op2"],
        )

    # works if input added, don't need to remove other stuff
    run_config["solids"]["op2"] = {"inputs": {"input_table": {"value": "public.table_1"}}}
    assert execute_pipeline(
        my_pipeline,
        run_config=run_config,
        solid_selection=["op2"],
    ).success

    # input for solid2 ignored if select solid1
    assert execute_pipeline(
        my_pipeline,
        run_config=run_config,
        solid_selection=["op1"],
    ).success


def test_extra_config_ignored_composites():
    @op(config_schema={"some_config": str})
    def op1(_):
        return "public.table_1"

    @composite_solid(
        config_schema={"wrapped_config": str},
        config_fn=lambda cfg: {"op1": {"config": {"some_config": cfg["wrapped_config"]}}},
    )
    def composite1():
        return op1()

    @op
    def op2(_, input_table="public.table"):
        return input_table

    @composite_solid
    def composite2(input_table):
        return op2(input_table)

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


def test_extra_config_input_bug():
    @op
    def root(_):
        return "public.table_1"

    @op(config_schema={"some_config": str})
    def takes_input(_, input_table):
        return input_table

    @pipeline
    def my_pipeline():
        takes_input(root())

    # Requires passing some config to the solid to bypass the
    # solid block level optionality
    run_config = {"solids": {"takes_input": {"config": {"some_config": "a"}}}}

    assert execute_pipeline(my_pipeline, run_config=run_config).success

    # Test against a bug where we generated required input config
    # for takes_input even though it was not being executed.
    assert execute_pipeline(
        my_pipeline,
        run_config=run_config,
        solid_selection=["root"],
    ).success

    # subselected pipeline shouldn't require the unselected solid's config
    assert execute_pipeline(
        my_pipeline,
        solid_selection=["root"],
    ).success


def test_extra_config_unsatisfied_input():
    @op
    def start(_, x):
        return x

    @op
    def end(_, x=1):
        return x

    @pipeline
    def testing():
        end(start())

    assert execute_pipeline(
        testing, run_config={"solids": {"start": {"inputs": {"x": {"value": 4}}}}}
    ).success

    # test to ensure that if start is not being executed its
    # input config is still allowed (and ignored)
    assert execute_pipeline(
        testing,
        run_config={"solids": {"start": {"inputs": {"x": {"value": 4}}}}},
        solid_selection=["end"],
    ).success


def test_extra_config_unsatisfied_input_io_man():
    @root_input_manager(input_config_schema=int)
    def config_io_man(context):
        return context.config

    @op(ins={"x": In(root_manager_key="my_loader")})
    def start(_, x):
        return x

    @op
    def end(_, x=1):
        return x

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_loader": config_io_man})])
    def testing_io():
        end(start())

    assert execute_pipeline(
        testing_io,
        run_config={
            "solids": {"start": {"inputs": {"x": 3}}},
        },
    ).success

    # test to ensure that if start is not being executed its
    # input config is still allowed (and ignored)
    assert execute_pipeline(
        testing_io,
        run_config={
            "solids": {"start": {"inputs": {"x": 3}}},
        },
        solid_selection=["end"],
    ).success


def test_config_with_no_schema():
    @op
    def my_op(context):
        assert context.op_config == 5

    @pipeline
    def my_pipeline():
        my_op()

    execute_pipeline(my_pipeline, run_config={"solids": {"my_op": {"config": 5}}})
