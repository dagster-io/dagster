from collections import defaultdict

import pytest

from dagster import DynamicOut, DynamicOutput, Int, Out, Output, graph, job, op, resource
from dagster._core.definitions import failure_hook, success_hook
from dagster._core.definitions.decorators.hook_decorator import event_list_hook
from dagster._core.definitions.events import Failure, HookExecutionResult
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._legacy import ModeDefinition, composite_solid, execute_pipeline, pipeline


class SomeUserException(Exception):
    pass


@resource
def resource_a(_init_context):
    return 1


def test_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook(required_resource_keys={"resource_a"})
    def a_hook(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        assert context.resources.resource_a == 1
        return HookExecutionResult("a_hook")

    @op
    def a_op(_):
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})])
    def a_pipeline():
        a_op.with_hooks(hook_defs={a_hook})()
        a_op.alias("solid_with_hook").with_hooks(hook_defs={a_hook})()
        a_op.alias("solid_without_hook")()

    result = execute_pipeline(a_pipeline)
    assert result.success
    assert called_hook_to_solids["a_hook"] == {"a_op", "solid_with_hook"}


def test_hook_accumulation():

    called_hook_to_step_keys = defaultdict(set)

    @event_list_hook
    def pipeline_hook(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step_key)
        return HookExecutionResult("pipeline_hook")

    @event_list_hook
    def solid_1_hook(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step_key)
        return HookExecutionResult("op_1_hook")

    @event_list_hook
    def composite_1_hook(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step_key)
        return HookExecutionResult("composite_1_hook")

    @op
    def op_1(_):
        return 1

    @op
    def op_2(_, num):
        return num

    @op
    def op_3(_):
        return 1

    @composite_solid
    def composite_1():
        return op_2(op_1.with_hooks({solid_1_hook})())

    @composite_solid
    def composite_2():
        op_3()
        return composite_1.with_hooks({composite_1_hook})()

    @pipeline_hook
    @pipeline
    def a_pipeline():
        composite_2()

    result = execute_pipeline(a_pipeline)
    assert result.success

    # make sure we gather hooks from all places and invoke them with the right steps
    assert called_hook_to_step_keys == {
        "pipeline_hook": {
            "composite_2.composite_1.op_1",
            "composite_2.composite_1.op_2",
            "composite_2.op_3",
        },
        "op_1_hook": {"composite_2.composite_1.op_1"},
        "composite_1_hook": {
            "composite_2.composite_1.op_1",
            "composite_2.composite_1.op_2",
        },
    }


def test_hook_on_composite_solid_instance():

    called_hook_to_step_keys = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step_key)
        return HookExecutionResult("hook_a_generic")

    @op
    def two(_):
        return 1

    @op
    def add_one(_, num):
        return num + 1

    @composite_solid
    def add_two():
        adder_1 = add_one.alias("adder_1")
        adder_2 = add_one.alias("adder_2")

        return adder_2(adder_1(two()))

    @pipeline
    def a_pipeline():
        add_two.with_hooks({hook_a_generic})()

    result = execute_pipeline(a_pipeline)
    assert result.success
    # the hook should run on all steps inside a composite
    assert called_hook_to_step_keys["hook_a_generic"] == set(
        [i.step_key for i in filter(lambda i: i.is_step_event, result.event_list)]
    )


def test_success_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @success_hook(required_resource_keys={"resource_a"})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        assert context.resources.resource_a == 1

    @op
    def a_op(_):
        pass

    @op
    def failed_op(_):
        raise SomeUserException()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})])
    def a_pipeline():
        a_op.with_hooks(hook_defs={a_hook})()
        a_op.alias("solid_with_hook").with_hooks(hook_defs={a_hook})()
        a_op.alias("solid_without_hook")()
        failed_op.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    assert called_hook_to_solids["a_hook"] == {"a_op", "solid_with_hook"}


def test_success_hook_on_solid_instance_subset():

    called_hook_to_solids = defaultdict(set)

    @success_hook(required_resource_keys={"resource_a"})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        assert context.resources.resource_a == 1

    @op
    def a_op(_):
        pass

    @op
    def failed_op(_):
        raise SomeUserException()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})])
    def a_pipeline():
        a_op.with_hooks(hook_defs={a_hook})()
        a_op.alias("solid_with_hook").with_hooks(hook_defs={a_hook})()
        a_op.alias("solid_without_hook")()
        failed_op.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(
        a_pipeline, raise_on_error=False, solid_selection=["a_op", "solid_with_hook"]
    )
    assert result.success
    assert called_hook_to_solids["a_hook"] == {"a_op", "solid_with_hook"}


def test_failure_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @failure_hook(required_resource_keys={"resource_a"})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        assert context.resources.resource_a == 1

    @op
    def failed_op(_):
        raise SomeUserException()

    @op
    def a_succeeded_op(_):
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})])
    def a_pipeline():
        failed_op.with_hooks(hook_defs={a_hook})()
        failed_op.alias("solid_with_hook").with_hooks(hook_defs={a_hook})()
        failed_op.alias("solid_without_hook")()
        a_succeeded_op.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    assert called_hook_to_solids["a_hook"] == {"failed_op", "solid_with_hook"}


def test_failure_hook_solid_exception():
    called = {}

    @failure_hook
    def a_hook(context):
        called[context.op.name] = context.op_exception

    @op
    def a_op(_):
        pass

    @op
    def user_code_error_op(_):
        raise SomeUserException()

    @op
    def failure_op(_):
        raise Failure()

    @a_hook
    @pipeline
    def a_pipeline():
        a_op()
        user_code_error_op()
        failure_op()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    assert "a_op" not in called
    assert isinstance(called.get("user_code_error_op"), SomeUserException)
    assert isinstance(called.get("failure_op"), Failure)


def test_none_solid_exception_access():
    called = {}

    @success_hook
    def a_hook(context):
        called[context.op.name] = context.op_exception

    @op
    def a_op(_):
        pass

    @a_hook
    @pipeline
    def a_pipeline():
        a_op()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert result.success
    assert called.get("a_op") is None


def test_solid_outputs_access():
    called = {}

    @success_hook
    def my_success_hook(context):
        called[context.step_key] = context.op_output_values

    @failure_hook
    def my_failure_hook(context):
        called[context.step_key] = context.op_output_values

    @op(out={"one": Out(), "two": Out(), "three": Out()})
    def a_op(_):
        yield Output(1, "one")
        yield Output(2, "two")
        yield Output(3, "three")

    @op(out={"one": Out(), "two": Out()})
    def failed_op(_):
        yield Output(1, "one")
        raise SomeUserException()
        yield Output(3, "two")  # pylint: disable=unreachable

    @op(out=DynamicOut())
    def dynamic_op(_):
        yield DynamicOutput(1, mapping_key="mapping_1")
        yield DynamicOutput(2, mapping_key="mapping_2")

    @op
    def echo(_, x):
        return x

    @my_success_hook
    @my_failure_hook
    @pipeline
    def a_pipeline():
        a_op()
        failed_op()
        dynamic_op().map(echo)

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    assert called.get("a_op") == {"one": 1, "two": 2, "three": 3}
    assert called.get("failed_op") == {"one": 1}
    assert called.get("dynamic_op") == {"result": {"mapping_1": 1, "mapping_2": 2}}
    assert called.get("echo[mapping_1]") == {"result": 1}
    assert called.get("echo[mapping_2]") == {"result": 2}


def test_hook_on_pipeline_def():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("hook_a_generic")

    @event_list_hook
    def hook_b_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("hook_b_generic")

    @op
    def op_a(_):
        pass

    @op
    def op_b(_):
        pass

    @op
    def op_c(_):
        pass

    @pipeline(hook_defs={hook_b_generic})
    def a_pipeline():
        op_a()
        op_b()
        op_c()

    result = execute_pipeline(a_pipeline.with_hooks({hook_a_generic}))
    assert result.success
    # the hook should run on all solids
    assert called_hook_to_solids == {
        "hook_b_generic": {"op_b", "op_a", "op_c"},
        "hook_a_generic": {"op_b", "op_a", "op_c"},
    }


def test_hook_on_pipeline_def_with_composite_solids():

    called_hook_to_step_keys = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step_key)
        return HookExecutionResult("hook_a_generic")

    @op
    def two(_):
        return 1

    @op
    def add_one(_, num):
        return num + 1

    @composite_solid
    def add_two():
        adder_1 = add_one.alias("adder_1")
        adder_2 = add_one.alias("adder_2")

        return adder_2(adder_1(two()))

    @pipeline
    def a_pipeline():
        add_two()

    hooked_pipeline = a_pipeline.with_hooks({hook_a_generic})
    # hooked_pipeline should be a copy of the original pipeline
    assert hooked_pipeline.top_level_solid_defs == a_pipeline.top_level_solid_defs
    assert hooked_pipeline.all_node_defs == a_pipeline.all_node_defs

    result = execute_pipeline(hooked_pipeline)
    assert result.success
    # the hook should run on all steps
    assert called_hook_to_step_keys["hook_a_generic"] == set(
        [i.step_key for i in filter(lambda i: i.is_step_event, result.event_list)]
    )


def test_hook_decorate_pipeline_def():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("hook_a_generic")

    @success_hook
    def hook_b_success(context):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)

    @failure_hook
    def hook_c_failure(context):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)

    @op
    def op_a(_):
        pass

    @op
    def op_b(_):
        pass

    @op
    def failed_op(_):
        raise SomeUserException()

    @hook_c_failure
    @hook_b_success
    @hook_a_generic
    @pipeline
    def a_pipeline():
        op_a()
        failed_op()
        op_b()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    # a generic hook runs on all solids
    assert called_hook_to_solids["hook_a_generic"] == {
        "op_a",
        "op_b",
        "failed_op",
    }
    # a success hook runs on all succeeded solids
    assert called_hook_to_solids["hook_b_success"] == {"op_a", "op_b"}
    # a failure hook runs on all failed solids
    assert called_hook_to_solids["hook_c_failure"] == {"failed_op"}


def test_hook_on_pipeline_def_and_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("hook_a_generic")

    @success_hook
    def hook_b_success(context):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)

    @failure_hook
    def hook_c_failure(context):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)

    @op
    def op_a(_):
        pass

    @op
    def op_b(_):
        pass

    @op
    def failed_op(_):
        raise SomeUserException()

    @hook_a_generic
    @pipeline
    def a_pipeline():
        op_a.with_hooks({hook_b_success})()
        failed_op.with_hooks({hook_c_failure})()
        # "hook_a_generic" should run on "solid_b" only once
        op_b.with_hooks({hook_a_generic})()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    # a generic hook runs on all solids
    assert called_hook_to_solids["hook_a_generic"] == {
        "op_a",
        "op_b",
        "failed_op",
    }
    # a success hook runs on "solid_a"
    assert called_hook_to_solids["hook_b_success"] == {"op_a"}
    # a failure hook runs on "failed_solid"
    assert called_hook_to_solids["hook_c_failure"] == {"failed_op"}
    hook_events = list(filter(lambda event: event.is_hook_event, result.event_list))
    # same hook will run once on the same solid invocation
    assert len(hook_events) == 5


def test_hook_context_config_schema():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def a_hook(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        assert context.op_config == {"config_1": 1}
        return HookExecutionResult("a_hook")

    @op(config_schema={"config_1": Int})
    def a_op(_):
        pass

    @pipeline
    def a_pipeline():
        a_op.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(
        a_pipeline, run_config={"solids": {"a_op": {"config": {"config_1": 1}}}}
    )
    assert result.success
    assert called_hook_to_solids["a_hook"] == {"a_op"}


def test_hook_resource_mismatch():
    @event_list_hook(required_resource_keys={"b"})
    def a_hook(context, _):
        assert context.resources.resource_a == 1
        return HookExecutionResult("a_hook")

    @op
    def a_op(_):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'b' required by hook 'a_hook' attached to pipeline '_' was not provided",
    ):

        @a_hook
        @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
        def _():
            a_op()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'b' required by hook 'a_hook' attached to solid 'a_op' was not provided",
    ):

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
        def _():
            a_op.with_hooks({a_hook})()


def test_hook_subpipeline():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("hook_a_generic")

    @op
    def op_a(_):
        pass

    @op
    def op_b(_):
        pass

    @hook_a_generic
    @pipeline
    def a_pipeline():
        op_a()
        op_b()

    result = execute_pipeline(a_pipeline)
    assert result.success
    # a generic hook runs on all solids
    assert called_hook_to_solids["hook_a_generic"] == {"op_a", "op_b"}

    called_hook_to_solids = defaultdict(set)

    result = execute_pipeline(a_pipeline, solid_selection=["op_a"])
    assert result.success
    assert called_hook_to_solids["hook_a_generic"] == {"op_a"}


def test_hook_ops():
    called_hook_to_ops = defaultdict(set)

    @success_hook
    def my_hook(context):
        called_hook_to_ops[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("my_hook")

    @op
    def a_op(_):
        pass

    @graph
    def a_graph():
        a_op.with_hooks(hook_defs={my_hook})()
        a_op.alias("op_with_hook").with_hooks(hook_defs={my_hook})()
        a_op.alias("op_without_hook")()

    result = a_graph.execute_in_process()
    assert result.success
    assert called_hook_to_ops["my_hook"] == {"a_op", "op_with_hook"}


def test_hook_graph():
    called_hook_to_ops = defaultdict(set)

    @success_hook
    def a_hook(context):
        called_hook_to_ops[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("a_hook")

    @success_hook
    def b_hook(context):
        called_hook_to_ops[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("a_hook")

    @op
    def a_op(_):
        pass

    @op
    def b_op(_):
        pass

    @a_hook
    @graph
    def sub_graph():
        a_op()

    @b_hook
    @graph
    def super_graph():
        sub_graph()
        b_op()

    result = super_graph.execute_in_process()
    assert result.success
    assert called_hook_to_ops["a_hook"] == {"a_op"}
    assert called_hook_to_ops["b_hook"] == {"a_op", "b_op"}

    # test to_job
    called_hook_to_ops = defaultdict(set)
    result = super_graph.to_job().execute_in_process()
    assert result.success
    assert called_hook_to_ops["a_hook"] == {"a_op"}
    assert called_hook_to_ops["b_hook"] == {"a_op", "b_op"}


def test_hook_on_job():
    called_hook_to_ops = defaultdict(set)

    @success_hook
    def a_hook(context):
        called_hook_to_ops[context.hook_def.name].add(context.op.name)
        return HookExecutionResult("a_hook")

    @op
    def basic():
        return 5

    @a_hook
    @job
    def hooked_job():
        basic()
        basic()
        basic()

    assert hooked_job.is_job  # Ensure that it's a job def, not a pipeline def
    result = hooked_job.execute_in_process()
    assert result.success
    assert called_hook_to_ops["a_hook"] == {"basic", "basic_2", "basic_3"}
