from collections import defaultdict

import pytest
from dagster import (
    DagsterEventType,
    ModeDefinition,
    PipelineDefinition,
    SolidInvocation,
    build_hook_context,
    check,
    execute_pipeline,
    graph,
    op,
    pipeline,
    reconstructable,
    resource,
    solid,
)
from dagster.core.definitions import NodeHandle, PresetDefinition, failure_hook, success_hook
from dagster.core.definitions.decorators.hook import event_list_hook
from dagster.core.definitions.events import HookExecutionResult
from dagster.core.definitions.policy import RetryPolicy
from dagster.core.errors import DagsterInvalidDefinitionError


@resource
def resource_a(_init_context):
    return 1


def test_hook_graph_job_op():
    called = {}
    op_output = "hook_op_output"

    @success_hook(required_resource_keys={"resource_a"})
    def hook_one(context):
        assert context.op.name
        called[context.hook_def.name] = called.get(context.hook_def.name, 0) + 1

    @success_hook()
    def hook_two(context):
        assert not context.op_config
        assert not context.op_exception
        assert context.op_output_values["result"] == op_output
        called[context.hook_def.name] = called.get(context.hook_def.name, 0) + 1

    @op
    def hook_op(_):
        return op_output

    ctx = build_hook_context(resources={"resource_a": resource_a}, op=hook_op)
    hook_one(ctx)
    assert called.get("hook_one") == 1

    @graph
    def run_success_hook():
        hook_op.with_hooks({hook_one, hook_two})()

    success_hook_job = run_success_hook.to_job(resource_defs={"resource_a": resource_a})
    assert success_hook_job.execute_in_process().success

    assert called.get("hook_one") == 2
    assert called.get("hook_two") == 1


def test_hook_context_op_solid_provided():
    @success_hook()
    def hook_one(context):
        pass

    @op
    def hook_op(_):
        pass

    with pytest.raises(check.CheckError):
        build_hook_context(op=hook_op, solid=hook_op)


def test_hook_decorator_graph_job_op():
    called_hook_to_solids = defaultdict(list)

    @success_hook
    def a_success_hook(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)

    @op
    def my_op(_):
        pass

    @graph
    def a_graph():
        my_op()

    assert a_graph.to_job(hooks={a_success_hook}).execute_in_process().success
    assert called_hook_to_solids["a_success_hook"][0] == "my_op"


def test_job_hook_context_job_name():
    my_job_name = "my_test_job_name"

    @success_hook
    def a_success_hook(context):
        assert context.job_name == my_job_name

    @graph
    def a_graph():
        pass

    assert a_graph.to_job(name=my_job_name, hooks={a_success_hook}).execute_in_process().success
