import pytest

from dagster import (
    ConfigMapping,
    DagsterInvalidConfigError,
    Field,
    In,
    String,
    graph,
    job,
    op,
    root_input_manager,
)


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

    @job
    def job_def():
        op_with_context()

    job_def.execute_in_process(
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

    @job
    def job_def():
        op_with_context()

    with pytest.raises(DagsterInvalidConfigError):
        job_def.execute_in_process(
            {"solids": {"op_with_context": {"config": {"some_config": 1}}}},
        )


def test_solid_not_found():
    @op(name="find_me_op", ins={}, out={})
    def find_me_op(_):
        raise Exception("should not reach")

    @job
    def job_def():
        find_me_op()

    with pytest.raises(DagsterInvalidConfigError):
        job_def.execute_in_process({"solids": {"not_found": {"config": {"some_config": 1}}}})


def test_extra_config_ignored_default_input():
    @op(config_schema={"some_config": str})
    def op1(_):
        return "public.table_1"

    @op
    def op2(_, input_table="public.table_1"):
        return input_table

    @job
    def my_job():
        op2(op1())

    run_config = {"solids": {"op1": {"config": {"some_config": "a"}}}}
    assert my_job.execute_in_process(run_config=run_config).success

    # same run config is valid even though solid1 not in subset
    assert my_job.execute_in_process(run_config=run_config, op_selection=["op2"]).success

    with pytest.raises(DagsterInvalidConfigError):
        # typos still raise, solid_1 instead of solid1
        my_job.execute_in_process(
            {"solids": {"solid_1": {"config": {"some_config": "a"}}}},
            op_selection=["op2"],
        )


def test_extra_config_ignored_no_default_input():
    @op(config_schema={"some_config": str})
    def op1(_):
        return "public.table_1"

    @op
    def op2(_, input_table):
        return input_table

    @job
    def my_job():
        op2(op1())

    run_config = {"solids": {"op1": {"config": {"some_config": "a"}}}}
    assert my_job.execute_in_process(run_config=run_config).success

    # run config is invalid since there is no input for solid2
    with pytest.raises(DagsterInvalidConfigError):
        my_job.execute_in_process(
            run_config=run_config,
            op_selection=["op2"],
        )

    # works if input added, don't need to remove other stuff
    run_config["solids"]["op2"] = {"inputs": {"input_table": {"value": "public.table_1"}}}
    assert my_job.execute_in_process(
        run_config=run_config,
        op_selection=["op2"],
    ).success

    # input for solid2 ignored if select solid1
    assert my_job.execute_in_process(
        run_config=run_config,
        op_selection=["op1"],
    ).success


def test_extra_config_ignored_composites():
    @op(config_schema={"some_config": str})
    def op1(_):
        return "public.table_1"

    @graph(
        config=ConfigMapping(
            config_schema={"wrapped_config": str},
            config_fn=lambda cfg: {"op1": {"config": {"some_config": cfg["wrapped_config"]}}},
        )
    )
    def graph1():
        return op1()

    @op
    def op2(_, input_table="public.table"):
        return input_table

    @graph
    def graph2(input_table):
        return op2(input_table)

    @job
    def my_job():
        graph2(graph1())

    run_config = {"solids": {"graph1": {"config": {"wrapped_config": "a"}}}}
    assert my_job.execute_in_process(run_config=run_config).success

    assert my_job.execute_in_process(run_config=run_config, op_selection=["graph2"]).success

    assert my_job.execute_in_process(run_config=run_config, op_selection=["graph1"]).success


def test_extra_config_input_bug():
    @op
    def root(_):
        return "public.table_1"

    @op(config_schema={"some_config": str})
    def takes_input(_, input_table):
        return input_table

    @job
    def my_job():
        takes_input(root())

    # Requires passing some config to the solid to bypass the
    # solid block level optionality
    run_config = {"solids": {"takes_input": {"config": {"some_config": "a"}}}}

    assert my_job.execute_in_process(run_config=run_config).success

    # Test against a bug where we generated required input config
    # for takes_input even though it was not being executed.
    assert my_job.execute_in_process(
        run_config=run_config,
        op_selection=["root"],
    ).success

    # subselected pipeline shouldn't require the unselected solid's config
    assert my_job.execute_in_process(
        op_selection=["root"],
    ).success


def test_extra_config_unsatisfied_input():
    @op
    def start(_, x):
        return x

    @op
    def end(_, x=1):
        return x

    @job
    def testing():
        end(start())

    assert testing.execute_in_process(
        run_config={"solids": {"start": {"inputs": {"x": {"value": 4}}}}}
    ).success

    # test to ensure that if start is not being executed its
    # input config is still allowed (and ignored)
    assert testing.execute_in_process(
        run_config={"solids": {"start": {"inputs": {"x": {"value": 4}}}}},
        op_selection=["end"],
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

    @job(resource_defs={"my_loader": config_io_man})
    def testing_io():
        end(start())

    assert testing_io.execute_in_process(
        run_config={
            "solids": {"start": {"inputs": {"x": 3}}},
        },
    ).success

    # test to ensure that if start is not being executed its
    # input config is still allowed (and ignored)
    assert testing_io.execute_in_process(
        run_config={
            "solids": {"start": {"inputs": {"x": 3}}},
        },
        op_selection=["end"],
    ).success


def test_config_with_no_schema():
    @op
    def my_op(context):
        assert context.op_config == 5

    @job
    def my_job():
        my_op()

    my_job.execute_in_process(run_config={"solids": {"my_op": {"config": 5}}})
