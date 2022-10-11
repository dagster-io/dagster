import warnings

import pytest

from dagster import (
    DependencyDefinition,
    GraphDefinition,
    GraphIn,
    GraphOut,
    In,
    Int,
    Nothing,
    OpDefinition,
    Out,
    Output,
    graph,
    job,
    op,
)
from dagster._core.definitions.decorators.hook_decorator import event_list_hook, success_hook
from dagster._core.definitions.events import DynamicOutput, HookExecutionResult
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.execution.api import create_execution_plan


def builder(graph):
    return graph.add_one(graph.return_one())


@op(out=Out(Int))
def echo(blah):
    return blah


@op
def return_one():
    return 1


@op
def return_two():
    return 2


@op
def return_tuple():
    return (1, 2)


@op(ins={"num": In()})
def add_one(num):
    return num + 1


@op(ins={"num": In()})
def pipe(num):
    return num


@op(
    ins={"int_1": In(Int), "int_2": In(Int)},
    out=Out(Int),
)
def adder(_context, int_1, int_2):
    return int_1 + int_2


@op(
    out={
        "one": Out(
            Int,
        ),
        "two": Out(
            Int,
        ),
    }
)
def return_mult(_context):
    yield Output(1, "one")
    yield Output(2, "two")


@op(config_schema=int)
def return_config_int(context):
    return context.op_config


def get_duplicate_ops():
    return (
        OpDefinition(name="a_op", ins={}, compute_fn=lambda: None, outs={}),
        OpDefinition(name="a_op", ins={}, compute_fn=lambda: None, outs={}),
    )


def test_basic():
    @graph
    def test():
        one = return_one()
        add_one(num=one)

    assert (
        GraphDefinition(node_defs=[test], name="test")
        .execute_in_process()
        .output_for_node("test.add_one")
        == 2
    )


def test_args():
    @graph
    def _test_1():
        one = return_one()
        add_one(one)

    @graph
    def _test_2():
        adder(return_one(), return_two())

    @graph
    def _test_3():
        adder(int_1=return_one(), int_2=return_two())

    @graph
    def _test_4():
        adder(return_one(), return_two())

    @graph
    def _test_5():
        adder(return_one(), int_2=return_two())

    @graph
    def _test_6():
        adder(return_one())

    @graph
    def _test_7():
        adder(int_2=return_two())


def test_arg_fails():

    with pytest.raises(DagsterInvalidDefinitionError):

        @graph
        def _fail_2():
            adder(return_one(), 1)

    with pytest.raises(DagsterInvalidDefinitionError):

        @graph
        def _fail_3():
            # pylint: disable=too-many-function-args
            adder(return_one(), return_two(), return_one.alias("three")())


def test_mult_out_fail():

    with pytest.raises(DagsterInvalidDefinitionError):

        @graph
        def _test():
            ret = return_mult()
            add_one(ret)


def test_aliased_with_name_name_fails():
    with pytest.raises(DagsterInvalidDefinitionError):

        @graph
        def _test():
            one, two = return_mult()
            add_one(num=one)
            add_one.alias("add_one")(num=two)  # explicit alias disables autoalias


def test_composite_with_duplicate_solids():
    solid_1, solid_2 = get_duplicate_ops()
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Detected conflicting node definitions with the same name",
    ):

        @graph
        def _name_conflict_graph():
            solid_1()
            solid_2()


def test_job_with_duplicate_solids():
    solid_1, solid_2 = get_duplicate_ops()
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Detected conflicting node definitions with the same name",
    ):

        @job
        def _name_conflict_job():
            solid_1()
            solid_2()


def test_multiple():
    @graph
    def test():
        one, two = return_mult()
        add_one(num=one)
        add_one.alias("add_one_2")(num=two)

    results = GraphDefinition(node_defs=[test], name="test").execute_in_process()
    assert results.output_for_node("test.add_one") == 2
    assert results.output_for_node("test.add_one_2") == 3


def test_two_inputs_with_dsl():
    @op(ins={"num_one": In(), "num_two": In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    @op
    def return_three():
        return 3

    @graph
    def test():
        subtract(num_one=return_two(), num_two=return_three())

    assert (
        GraphDefinition(node_defs=[test], name="test")
        .execute_in_process()
        .output_for_node("test.subtract")
        == -1
    )


def test_basic_aliasing_with_dsl():
    @graph
    def test():
        add_one.alias("renamed")(num=return_one())

    assert (
        GraphDefinition(node_defs=[test], name="test")
        .execute_in_process()
        .output_for_node("test.renamed")
        == 2
    )


def test_diamond_graph():
    @op(out={"value_one": Out(), "value_two": Out()})
    def emit_values(_context):
        yield Output(1, "value_one")
        yield Output(2, "value_two")

    @op(ins={"num_one": In(), "num_two": In()})
    def subtract(num_one, num_two):
        return num_one - num_two

    @graph
    def diamond():
        value_one, value_two = emit_values()
        subtract(
            num_one=add_one(num=value_one),
            num_two=add_one.alias("renamed")(num=value_two),
        )

    result = GraphDefinition(node_defs=[diamond], name="test").execute_in_process()

    assert result.output_for_node("diamond.subtract") == -1


def test_mapping():
    @op(
        ins={"num_in": In(Int)},
        out={
            "num_out": Out(
                Int,
            )
        },
    )
    def double(num_in):
        return num_in * 2

    @graph(
        ins={"num_in": GraphIn()},
        out={"num_out": GraphOut()},
    )
    def composed_inout(num_in):
        return double(num_in=num_in)

    assert (
        GraphDefinition(
            node_defs=[return_one, composed_inout],
            name="test",
            dependencies={
                "composed_inout": {"num_in": DependencyDefinition("return_one")},
            },
        )
        .execute_in_process()
        .output_for_node("composed_inout", output_name="num_out")
        == 2
    )


def test_mapping_args_kwargs():
    @op
    def take(a, b, c):
        return (a, b, c)

    @graph
    def maps(m_c, m_b, m_a):
        take(m_a, b=m_b, c=m_c)

    assert maps.input_mappings[2].graph_input_name == "m_a"
    assert maps.input_mappings[2].maps_to.input_name == "a"

    assert maps.input_mappings[1].graph_input_name == "m_b"
    assert maps.input_mappings[1].maps_to.input_name == "b"

    assert maps.input_mappings[0].graph_input_name == "m_c"
    assert maps.input_mappings[0].maps_to.input_name == "c"


def test_output_map_mult():
    @graph(out={"one": GraphOut(), "two": GraphOut()})
    def wrap_mult():
        return return_mult()

    @graph
    def mult_graph():
        one, two = wrap_mult()
        echo.alias("echo_one")(one)
        echo.alias("echo_two")(two)

    result = mult_graph.execute_in_process()
    assert result.output_for_node("echo_one") == 1
    assert result.output_for_node("echo_two") == 2


def test_output_map_mult_swizzle():
    @graph(out={"x": GraphOut(), "y": GraphOut()})
    def wrap_mult():
        one, two = return_mult()
        return {"x": one, "y": two}

    @graph
    def mult_graph():
        x, y = wrap_mult()
        echo.alias("echo_x")(x)
        echo.alias("echo_y")(y)

    result = mult_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("echo_x") == 1
    assert result.output_for_node("echo_y") == 2


def test_output_map_implicit_ordering():
    @graph(out={"three": GraphOut(), "four": GraphOut()})
    def _implicit():
        return return_mult()

    result = _implicit.execute_in_process()
    assert result.output_value("three") == 1
    assert result.output_value("four") == 2


def test_output_map_fail():
    with pytest.raises(DagsterInvalidDefinitionError):

        @graph(out={"one": GraphOut(), "two": GraphOut()})
        def _bad(_context):
            return return_one()

    with pytest.raises(DagsterInvalidDefinitionError):

        @graph(out={"one": GraphOut(), "two": GraphOut()})
        def _bad(_context):
            return {"one": 1}


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

    @op(ins={"num": In()}, out=Out(Int))
    def load_num(num):
        return num + 3

    @graph
    def test():
        return load_num(
            num=canonicalize_num(
                num=subsample_num(num=ingest_num(num=unzip_num(num=download_num())))
            )
        )

    result = GraphDefinition(node_defs=[test], name="test").execute_in_process(
        run_config={"ops": {"test": {"solids": {"download_num": {"config": 123}}}}}
    )
    assert result.output_for_node("test.canonicalize_num") == 123
    assert result.output_for_node("test.load_num") == 126


def test_recursion():
    @graph
    def outer():
        @graph
        def inner():
            return add_one(return_one())

        add_one(inner())

    assert GraphDefinition(node_defs=[outer], name="test").execute_in_process().success


class Garbage(Exception):
    pass


def test_recursion_with_exceptions():
    called = {}

    @graph
    def recurse():
        @graph
        def outer():
            try:

                @graph
                def throws():
                    called["throws"] = True
                    raise Garbage()

                throws()
            except Garbage:
                add_one(return_one())

        outer()

    assert recurse.execute_in_process().success
    assert called["throws"] is True


def test_job_has_solid_def():
    @graph
    def inner():
        return add_one(return_one())

    @graph
    def outer():
        add_one(inner())

    @job
    def a_job():
        outer()

    assert a_job.has_solid_def("add_one")
    assert a_job.has_solid_def("outer")
    assert a_job.has_solid_def("inner")


def test_mapping_args_ordering():
    @op
    def take(a, b, c):
        assert a == "a"
        assert b == "b"
        assert c == "c"

    @graph
    def swizzle(b, a, c):
        take(a, b, c)

    @graph
    def swizzle_2(c, b, a):
        swizzle(b, a=a, c=c)

    @graph
    def ordered():
        swizzle_2()

    for mapping in swizzle.input_mappings:
        assert mapping.graph_input_name == mapping.maps_to.input_name

    for mapping in swizzle_2.input_mappings:
        assert mapping.graph_input_name == mapping.maps_to.input_name

    ordered.execute_in_process(
        run_config={
            "ops": {
                "swizzle_2": {
                    "inputs": {
                        "a": {"value": "a"},
                        "b": {"value": "b"},
                        "c": {"value": "c"},
                    }
                }
            }
        },
    )


def test_unused_mapping():
    with pytest.raises(DagsterInvalidDefinitionError, match="unmapped input"):

        @graph
        def unused_mapping(_):
            return_one()


@op
def single_input_op():
    return


def test_collision_invocations():
    with pytest.warns(None) as record:

        @job
        def _():
            single_input_op()
            single_input_op()
            single_input_op()

    assert len(record) == 0


def test_alias_invoked(recwarn):
    @job
    def _():
        single_input_op.alias("foo")()
        single_input_op.alias("bar")()

    assert len(recwarn) == 0


def test_alias_not_invoked():

    with pytest.warns(UserWarning, match="received an uninvoked op") as record:

        @job
        def _my_job():
            single_input_op.alias("foo")
            single_input_op.alias("bar")

    assert len(record) == 2  # This job should raise a warning for each aliasing of the solid.


def test_tag_invoked():

    # See: https://docs.pytest.org/en/7.0.x/how-to/capture-warnings.html#additional-use-cases-of-warnings-in-tests
    with warnings.catch_warnings():
        warnings.simplefilter("error", category=UserWarning)

        @graph
        def _my_graph():
            single_input_op.tag({})()

        _my_graph.execute_in_process()


def test_tag_not_invoked():

    with pytest.warns(
        UserWarning,
        match="uninvoked op",
    ) as record:

        @job
        def _my_job():
            single_input_op.tag({})
            single_input_op.tag({})

        _my_job.execute_in_process()

    user_warnings = [warning for warning in record if isinstance(warning.message, UserWarning)]
    assert (
        len(user_warnings) == 1
    )  # We should only raise one warning because solids have same name.

    with pytest.warns(UserWarning, match="uninvoked op"):

        @job
        def _my_job():
            single_input_op.tag({"a": "b"})

        _my_job.execute_in_process()


def test_with_hooks_invoked():

    with warnings.catch_warnings():
        warnings.simplefilter("error", category=UserWarning)

        @job
        def _my_job():
            single_input_op.with_hooks(set())()

        _my_job.execute_in_process()


@event_list_hook(required_resource_keys=set())
def a_hook(_context, _):
    return HookExecutionResult("a_hook")


def test_with_hooks_not_invoked():
    with pytest.warns(
        UserWarning,
        match="uninvoked op",
    ) as record:

        @job
        def _my_job():
            single_input_op.with_hooks(set())
            single_input_op.with_hooks(set())

        _my_job.execute_in_process()

    # Note not returning out of the pipe causes warning count to go up to 2
    user_warnings = [warning for warning in record if isinstance(warning.message, UserWarning)]
    assert (
        len(user_warnings) == 1
    )  # We should only raise one warning because solids have same name.

    with pytest.warns(
        UserWarning,
        match="uninvoked op",
    ):

        @job
        def _my_job():
            single_input_op.with_hooks({a_hook})

        _my_job.execute_in_process()


def test_with_hooks_not_empty():
    @job
    def _():
        single_input_op.with_hooks({a_hook})

    assert 1 == 1


def test_multiple_pending_invocations():
    with pytest.warns(
        UserWarning,
        match="uninvoked op",
    ) as record:

        @job
        def _my_job():
            foo = single_input_op.alias("foo")
            bar = single_input_op.alias("bar")
            foo_tag = foo.tag({})
            _bar_hook = bar.with_hooks({a_hook})
            foo_tag()

    assert (
        len(record) == 1
    )  # ensure that one warning is thrown per solid_name / alias instead of per every PendingNodeInvocation.


def test_compose_nothing():
    @op(ins={"start": In(Nothing)})
    def go():
        pass

    @graph(ins={"start": GraphIn()})
    def _compose(start: Nothing):
        go(start)  # pylint: disable=too-many-function-args


def test_multimap():
    @graph(out={"x": GraphOut(), "y": GraphOut()})
    def multimap(foo):
        x = echo.alias("echo_1")(foo)
        y = echo.alias("echo_2")(foo)
        return {"x": x, "y": y}

    @job
    def multimap_pipe():
        one = return_one()
        multimap(one)

    result = multimap_pipe.execute_in_process()
    assert result.output_for_node("multimap.echo_1") == 1
    assert result.output_for_node("multimap.echo_2") == 1


def test_reuse_inputs():
    @graph(ins={"one": GraphIn(), "two": GraphIn()})
    def calculate(one, two):
        adder(one, two)
        adder.alias("adder_2")(one, two)

    @job
    def calculate_job():
        one = return_one()
        two = return_two()
        calculate(one, two)

    result = calculate_job.execute_in_process()
    assert result.output_for_node("calculate.adder") == 3
    assert result.output_for_node("calculate.adder_2") == 3


def test_output_node_error():
    with pytest.raises(DagsterInvariantViolationError):

        @job
        def _bad_destructure():
            _a, _b = return_tuple()

    with pytest.raises(DagsterInvariantViolationError):

        @job
        def _bad_index():
            out = return_tuple()
            add_one(out[0])


def test_job_composition_metadata():
    @op
    def metadata_op(context):
        return context.op.tags["key"]

    @job
    def metadata_test_job():
        metadata_op.tag({"key": "foo"}).alias("aliased_one")()
        metadata_op.alias("aliased_two").tag({"key": "foo"}).tag({"key": "bar"})()
        metadata_op.alias("aliased_three").tag({"key": "baz"})()
        metadata_op.tag({"key": "quux"})()

    res = metadata_test_job.execute_in_process()

    assert res.output_for_node("aliased_one") == "foo"
    assert res.output_for_node("aliased_two") == "bar"
    assert res.output_for_node("aliased_three") == "baz"
    assert res.output_for_node("metadata_op") == "quux"


def test_composition_metadata():
    @op
    def metadata_op(context):
        return context.op.tags["key"]

    @graph
    def metadata_graph():
        metadata_op.tag({"key": "foo"}).alias("aliased_one")()
        metadata_op.alias("aliased_two").tag({"key": "foo"}).tag({"key": "bar"})()
        metadata_op.alias("aliased_three").tag({"key": "baz"})()
        metadata_op.tag({"key": "quux"})()

    @job
    def metadata_test_job():
        metadata_graph()

    res = metadata_test_job.execute_in_process()

    assert res.output_for_node("metadata_graph.aliased_one") == "foo"
    assert res.output_for_node("metadata_graph.aliased_two") == "bar"
    assert res.output_for_node("metadata_graph.aliased_three") == "baz"
    assert res.output_for_node("metadata_graph.metadata_op") == "quux"


def test_uninvoked_solid_fails():
    with pytest.raises(DagsterInvalidDefinitionError, match=r".*Did you forget parentheses?"):

        @job
        def uninvoked_solid_job():
            add_one(return_one)

        uninvoked_solid_job.execute_in_process()


def test_uninvoked_aliased_solid_fails():
    with pytest.raises(DagsterInvalidDefinitionError, match=r".*Did you forget parentheses?"):

        @job
        def uninvoked_aliased_solid_job():
            add_one(return_one.alias("something"))

        uninvoked_aliased_solid_job.execute_in_process()


def test_alias_on_invoked_solid_fails():
    with pytest.raises(
        DagsterInvariantViolationError,
        match=r".*Consider checking the location of parentheses.",
    ):

        @job
        def alias_on_invoked_solid_job():
            return_one().alias("something")  # pylint: disable=no-member

        alias_on_invoked_solid_job.execute_in_process()


def test_tags():
    @op(tags={"def": "1"})
    def emit(_):
        return 1

    @job
    def tag():
        emit.tag({"invoke": "2"})()

    plan = create_execution_plan(tag)
    step = list(plan.step_dict.values())[0]
    assert step.tags == {"def": "1", "invoke": "2"}


def test_bad_alias():
    with pytest.raises(DagsterInvalidDefinitionError, match="not a valid name"):
        echo.alias("uh oh")

    with pytest.raises(DagsterInvalidDefinitionError, match="not a valid name"):
        echo.alias("uh[oh]")


def test_tag_subset():
    @op
    def empty(_):
        pass

    @op(tags={"def": "1"})
    def emit(_):
        return 1

    @job
    def tag():
        empty()
        emit.tag({"invoke": "2"})()

    plan = create_execution_plan(tag.get_job_def_for_subset_selection(["emit"]))
    step = list(plan.step_dict.values())[0]
    assert step.tags == {"def": "1", "invoke": "2"}


def test_composition_order():
    solid_to_tags = {}

    @success_hook
    def test_hook(context):
        solid_to_tags[context.op.name] = context.op.tags

    @op
    def a_op(_):
        pass

    @job
    def a_job():
        a_op.with_hooks(hook_defs={test_hook}).alias("hook_alias_tag").tag({"pos": 3})()
        a_op.with_hooks(hook_defs={test_hook}).tag({"pos": 2}).alias("hook_tag_alias")()
        a_op.alias("alias_tag_hook").tag({"pos": 2}).with_hooks(hook_defs={test_hook})()
        a_op.alias("alias_hook_tag").with_hooks(hook_defs={test_hook}).tag({"pos": 3})()
        a_op.tag({"pos": 1}).with_hooks(hook_defs={test_hook}).alias("tag_hook_alias")()
        a_op.tag({"pos": 1}).alias("tag_alias_hook").with_hooks(hook_defs={test_hook})()

    result = a_job.execute_in_process(raise_on_error=False)
    assert result.success
    assert solid_to_tags == {
        "tag_hook_alias": {"pos": "1"},
        "tag_alias_hook": {"pos": "1"},
        "hook_tag_alias": {"pos": "2"},
        "alias_tag_hook": {"pos": "2"},
        "hook_alias_tag": {"pos": "3"},
        "alias_hook_tag": {"pos": "3"},
    }


def test_fan_in_scalars_fails():
    @op
    def fan_in_op(_, xs):
        return sum(xs)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Lists can only contain the output from previous solid invocations or input mappings",
    ):

        @job
        def _scalar_fan_in_job():
            fan_in_op([1, 2, 3])


def test_with_hooks_on_invoked_solid_fails():
    @op
    def yield_1_op(_):
        return 1

    with pytest.raises(
        DagsterInvariantViolationError,
        match="attempted to call hook method for InvokedSolidOutputHandle.",
    ):

        @job
        def _bad_hooks_job():
            yield_1_op().with_hooks({a_hook})


def test_iterating_over_dynamic_outputs_fails():
    @op
    def dynamic_output_op(_):
        yield DynamicOutput(1, "1")
        yield DynamicOutput(2, "2")

    @op
    def yield_input(_, x):
        return x

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to iterate over an InvokedSolidOutputHandle.",
    ):

        @job
        def _iterating_over_dynamic_output_job():
            for x in dynamic_output_op():
                yield_input(x)


def test_indexing_into_dynamic_outputs_fails():
    @op
    def dynamic_output_op(_):
        yield DynamicOutput(1, "1")
        yield DynamicOutput(2, "2")

    @op
    def yield_input(_, x):
        return x

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to index in to an InvokedSolidOutputHandle.",
    ):

        @job
        def _indexing_into_dynamic_output_job():
            yield_input(dynamic_output_op()[0])


def test_aliasing_invoked_dynamic_output_fails():
    @op
    def dynamic_output_op(_):
        yield DynamicOutput(1, "1")
        yield DynamicOutput(2, "2")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="attempted to call alias method for InvokedSolidOutputHandle.",
    ):

        @job
        def _alias_invoked_dynamic_output_job():
            dynamic_output_op().alias("dynamic_output")
