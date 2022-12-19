import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    GraphDefinition,
    In,
    Int,
    Out,
    Output,
    graph,
    job,
    op,
    usable_as_dagster_type,
)


def builder(graph):
    return graph.add_one(graph.return_one())


@op
def return_one():
    return 1


@op
def return_two():
    return 2


@op
def return_three():
    return 3


@op(ins={"num": In()})
def add_one(num):
    return num + 1


def test_basic_use_case():
    graph_def = GraphDefinition(
        name="basic",
        node_defs=[return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )

    assert graph_def.execute_in_process().output_for_node("add_one") == 2


def test_basic_use_case_with_dsl():
    @job
    def test():
        add_one(num=return_one())

    assert test.execute_in_process().output_for_node("add_one") == 2


def test_two_inputs_without_dsl():
    @op(ins={"num_one": In(), "num_two": In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    graph_def = GraphDefinition(
        node_defs=[subtract, return_two, return_three],
        name="test",
        dependencies={
            "subtract": {
                "num_one": DependencyDefinition("return_two"),
                "num_two": DependencyDefinition("return_three"),
            }
        },
    )

    assert graph_def.execute_in_process().output_for_node("subtract") == -1


def test_two_inputs_with_dsl():
    @op(ins={"num_one": In(), "num_two": In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    @job
    def test():
        subtract(num_one=return_two(), num_two=return_three())

    assert test.execute_in_process().output_for_node("subtract") == -1


def test_basic_aliasing_with_dsl():
    @job
    def test():
        add_one.alias("renamed")(num=return_one())

    assert test.execute_in_process().output_for_node("renamed") == 2


def test_diamond_graph():
    @op(out={"value_one": Out(), "value_two": Out()})
    def emit_values(_context):
        yield Output(1, "value_one")
        yield Output(2, "value_two")

    @op(ins={"num_one": In(), "num_two": In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    @job
    def diamond_job():
        value_one, value_two = emit_values()
        subtract(
            num_one=add_one(num=value_one),
            num_two=add_one.alias("renamed")(num=value_two),
        )

    result = diamond_job.execute_in_process()

    assert result.output_for_node("subtract") == -1


def test_two_cliques():
    @job
    def diamond_job():
        return_one()
        return_two()

    result = diamond_job.execute_in_process()

    assert result.output_for_node("return_one") == 1
    assert result.output_for_node("return_two") == 2


def test_deep_graph():
    @op(config_schema=Int)
    def download_num(context):
        return context.op_config

    @op(ins={"num": In()})
    def unzip_num(num):
        return num

    @op(ins={"num": In()})
    def ingest_num(num):
        return num

    @op(ins={"num": In()})
    def subsample_num(num):
        return num

    @op(ins={"num": In()})
    def canonicalize_num(num):
        return num

    @op(ins={"num": In()})
    def load_num(num):
        return num + 3

    @job
    def test():
        load_num(
            num=canonicalize_num(
                num=subsample_num(num=ingest_num(num=unzip_num(num=download_num())))
            )
        )

    result = test.execute_in_process(run_config={"ops": {"download_num": {"config": 123}}})
    assert result.output_for_node("canonicalize_num") == 123
    assert result.output_for_node("load_num") == 126


def test_unconfigurable_inputs_pipeline():
    @usable_as_dagster_type
    class NewType:
        pass

    @op(ins={"_unused": In(NewType)})
    def noop(_unused):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Input '_unused' of op 'noop' has no way of being resolved",
    ):

        @job
        def _bad_inputs():
            noop()


def test_dupe_defs_fail():
    @op(name="same")
    def noop():
        pass

    @op(name="same")
    def noop2():
        pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @job
        def _dupes():
            noop()
            noop2()

    with pytest.raises(DagsterInvalidDefinitionError):
        GraphDefinition(name="dupes", node_defs=[noop, noop2]).to_job()


def test_composite_dupe_defs_fail():
    @op
    def noop():
        pass

    @graph(name="same")
    def graph_noop():
        noop()
        noop()
        noop()

    @graph(name="same")
    def graph_noop2():
        noop()

    @graph
    def wrapper():
        graph_noop2()

    @graph
    def top():
        wrapper()
        graph_noop()

    with pytest.raises(DagsterInvalidDefinitionError):

        @job
        def _dupes():
            graph_noop()
            graph_noop2()

    with pytest.raises(DagsterInvalidDefinitionError):
        GraphDefinition(name="dupes", node_defs=[top]).to_job()


def test_two_inputs_with_reversed_input_defs_and_dsl():
    @op(ins={"num_two": In(), "num_one": In()})
    def subtract_ctx(_context, num_one, num_two):
        return num_one - num_two

    @op(ins={"num_two": In(), "num_one": In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    @job
    def test():
        two = return_two()
        three = return_three()
        subtract(two, three)
        subtract_ctx(two, three)

    result = test.execute_in_process()
    assert result.output_for_node("subtract") == -1
    assert result.output_for_node("subtract_ctx") == -1


def test_single_non_positional_input_use():
    @op(ins={"num": In()})
    def add_one_kw(**kwargs):
        return kwargs["num"] + 1

    @job
    def test():
        # the decorated solid fn doesn't define args
        # but since there is only one it is unambiguous
        add_one_kw(return_two())

    assert test.execute_in_process().output_for_node("add_one_kw") == 3


def test_single_positional_single_kwarg_input_use():
    @op(ins={"num_two": In(), "num_one": In()})
    def subtract_kw(num_one, **kwargs):
        return num_one - kwargs["num_two"]

    @job
    def test():
        # the decorated solid fn only defines one positional arg
        # and one kwarg so passing two by position is unambiguous
        # since the second argument must be the one kwarg
        subtract_kw(return_two(), return_three())

    assert test.execute_in_process().output_for_node("subtract_kw") == -1


def test_bad_positional_input_use():
    @op(ins={"num_two": In(), "num_one": In(), "num_three": In()})
    def add_kw(num_one, **kwargs):
        return num_one + kwargs["num_two"] + kwargs["num_three"]

    with pytest.raises(DagsterInvalidDefinitionError, match="Use keyword args instead"):

        @job
        def _fail():
            # the decorated solid fn only defines one positional arg
            # so the two remaining have no positions and this is
            # ambiguous
            add_kw(return_two(), return_two(), return_two())
