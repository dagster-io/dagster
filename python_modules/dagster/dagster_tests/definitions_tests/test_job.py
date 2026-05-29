import dagster as dg
import pytest
from dagster import Int


def builder(graph):
    return graph.add_one(graph.return_one())


@dg.op
def return_one():
    return 1


@dg.op
def return_two():
    return 2


@dg.op
def return_three():
    return 3


@dg.op(ins={"num": dg.In()})
def add_one(num):
    return num + 1


def test_basic_use_case():
    graph_def = dg.GraphDefinition(
        name="basic",
        node_defs=[return_one, add_one],
        dependencies={"add_one": {"num": dg.DependencyDefinition("return_one")}},
    )

    assert graph_def.execute_in_process().output_for_node("add_one") == 2


def test_basic_use_case_with_dsl():
    @dg.job
    def test():
        add_one(num=return_one())

    assert test.execute_in_process().output_for_node("add_one") == 2


def test_two_inputs_without_dsl():
    @dg.op(ins={"num_one": dg.In(), "num_two": dg.In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    graph_def = dg.GraphDefinition(
        node_defs=[subtract, return_two, return_three],
        name="test",
        dependencies={
            "subtract": {
                "num_one": dg.DependencyDefinition("return_two"),
                "num_two": dg.DependencyDefinition("return_three"),
            }
        },
    )

    assert graph_def.execute_in_process().output_for_node("subtract") == -1


def test_two_inputs_with_dsl():
    @dg.op(ins={"num_one": dg.In(), "num_two": dg.In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    @dg.job
    def test():
        subtract(num_one=return_two(), num_two=return_three())

    assert test.execute_in_process().output_for_node("subtract") == -1


def test_basic_aliasing_with_dsl():
    @dg.job
    def test():
        add_one.alias("renamed")(num=return_one())

    assert test.execute_in_process().output_for_node("renamed") == 2


def test_diamond_graph():
    @dg.op(out={"value_one": dg.Out(), "value_two": dg.Out()})
    def emit_values(_context):
        yield dg.Output(1, "value_one")
        yield dg.Output(2, "value_two")

    @dg.op(ins={"num_one": dg.In(), "num_two": dg.In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    @dg.job
    def diamond_job():
        value_one, value_two = emit_values()
        subtract(
            num_one=add_one(num=value_one),
            num_two=add_one.alias("renamed")(num=value_two),
        )

    result = diamond_job.execute_in_process()

    assert result.output_for_node("subtract") == -1


def test_two_cliques():
    @dg.job
    def diamond_job():
        return_one()
        return_two()

    result = diamond_job.execute_in_process()

    assert result.output_for_node("return_one") == 1
    assert result.output_for_node("return_two") == 2


def test_deep_graph():
    @dg.op(config_schema=Int)
    def download_num(context):
        return context.op_config

    @dg.op(ins={"num": dg.In()})
    def unzip_num(num):
        return num

    @dg.op(ins={"num": dg.In()})
    def ingest_num(num):
        return num

    @dg.op(ins={"num": dg.In()})
    def subsample_num(num):
        return num

    @dg.op(ins={"num": dg.In()})
    def canonicalize_num(num):
        return num

    @dg.op(ins={"num": dg.In()})
    def load_num(num):
        return num + 3

    @dg.job
    def test():
        load_num(
            num=canonicalize_num(
                num=subsample_num(num=ingest_num(num=unzip_num(num=download_num())))
            )
        )

    result = test.execute_in_process(run_config={"ops": {"download_num": {"config": 123}}})
    assert result.output_for_node("canonicalize_num") == 123
    assert result.output_for_node("load_num") == 126


def test_unconfigurable_inputs_job():
    @dg.usable_as_dagster_type
    class NewType:
        pass

    @dg.op(ins={"_unused": dg.In(NewType)})
    def noop(_unused):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Input '_unused' of op 'noop' has no way of being resolved",
    ):

        @dg.job
        def _bad_inputs():
            noop()


def test_dupe_defs_fail():
    @dg.op(name="same")
    def noop():
        pass

    @dg.op(name="same")
    def noop2():
        pass

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.job
        def _dupes():
            noop()
            noop2()

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        dg.GraphDefinition(name="dupes", node_defs=[noop, noop2]).to_job()


def test_composite_dupe_defs_fail():
    @dg.op
    def noop():
        pass

    @dg.graph(name="same")
    def graph_noop():
        noop()
        noop()
        noop()

    @dg.graph(name="same")
    def graph_noop2():
        noop()

    @dg.graph
    def wrapper():
        graph_noop2()

    @dg.graph
    def top():
        wrapper()
        graph_noop()

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.job
        def _dupes():
            graph_noop()
            graph_noop2()

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        dg.GraphDefinition(name="dupes", node_defs=[top]).to_job()


def test_two_inputs_with_reversed_input_defs_and_dsl():
    @dg.op(ins={"num_two": dg.In(), "num_one": dg.In()})
    def subtract_ctx(_context, num_one, num_two):
        return num_one - num_two

    @dg.op(ins={"num_two": dg.In(), "num_one": dg.In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    @dg.job
    def test():
        two = return_two()
        three = return_three()
        subtract(two, three)
        subtract_ctx(two, three)

    result = test.execute_in_process()
    assert result.output_for_node("subtract") == -1
    assert result.output_for_node("subtract_ctx") == -1


def test_single_non_positional_input_use():
    @dg.op(ins={"num": dg.In()})
    def add_one_kw(**kwargs):
        return kwargs["num"] + 1

    @dg.job
    def test():
        # the decorated solid fn doesn't define args
        # but since there is only one it is unambiguous
        add_one_kw(return_two())

    assert test.execute_in_process().output_for_node("add_one_kw") == 3


def test_single_positional_single_kwarg_input_use():
    @dg.op(ins={"num_two": dg.In(), "num_one": dg.In()})
    def subtract_kw(num_one, **kwargs):
        return num_one - kwargs["num_two"]

    @dg.job
    def test():
        # the decorated solid fn only defines one positional arg
        # and one kwarg so passing two by position is unambiguous
        # since the second argument must be the one kwarg
        subtract_kw(return_two(), return_three())

    assert test.execute_in_process().output_for_node("subtract_kw") == -1


def test_bad_positional_input_use():
    @dg.op(ins={"num_two": dg.In(), "num_one": dg.In(), "num_three": dg.In()})
    def add_kw(num_one, **kwargs):
        return num_one + kwargs["num_two"] + kwargs["num_three"]

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Use keyword args instead"):

        @dg.job
        def _fail():
            # the decorated solid fn only defines one positional arg
            # so the two remaining have no positions and this is
            # ambiguous
            add_kw(return_two(), return_two(), return_two())


def test_job_recreation_works() -> None:
    @dg.op(config_schema={"foo": str})
    def requires_config(_):
        pass

    @dg.job
    def job_requires_config():
        requires_config()

    result = dg.validate_run_config(
        job_requires_config.with_executor_def(dg.in_process_executor),
        {"ops": {"requires_config": {"config": {"foo": "bar"}}}},
    )
    # Ensure that the validated config has an in_process_executor execution entry
    assert result == {
        "ops": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {"in_process": {"retries": {"enabled": {}}}},
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }


def test_metadata():
    @dg.job(metadata={"foo": "bar", "four": 4})
    def original(): ...

    assert original.metadata["foo"] == dg.TextMetadataValue("bar")
    assert original.metadata["four"] == dg.IntMetadataValue(4)

    blanked = original.with_metadata({})
    assert blanked.metadata == {}

    updated = original.with_metadata({**original.metadata, "foo": "baz"})
    assert updated.metadata["foo"] == dg.TextMetadataValue("baz")
    assert updated.metadata["four"] == dg.IntMetadataValue(4)


def test_owners():
    @dg.job(owners=["user@example.com", "team:data"])
    def job_with_owners(): ...

    assert job_with_owners.owners == ["user@example.com", "team:data"]


def test_owners_validation():
    # Test that invalid owners are rejected

    # Test invalid team name with special characters
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="contains invalid characters"):

        @dg.job(owners=["team:bad-name"])
        def job_with_bad_team(): ...

    # Test empty team name
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Team name cannot be empty"):

        @dg.job(owners=["team:"])
        def job_with_empty_team(): ...

    # Test invalid owner format
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Owner must be an email address"):

        @dg.job(owners=["not-an-email-or-team"])
        def job_with_invalid_owner(): ...
