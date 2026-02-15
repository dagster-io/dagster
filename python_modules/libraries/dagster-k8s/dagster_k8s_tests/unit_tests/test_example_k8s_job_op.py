# ruff: isort: skip_file
# fmt: off
# start_marker
from dagster_k8s import k8s_job_op
from dagster_k8s.ops.k8s_job_op import execute_k8s_job as _execute_k8s_job
from dagster_k8s.job import K8sConfigMergeBehavior


from dagster import job, OpExecutionContext, DagsterRun, build_op_context

from unittest import mock

# Example ops from the original file
first_op_example = k8s_job_op.configured(
    {
        "image": "busybox",
        "command": ["/bin/sh", "-c"],
        "args": ["echo HELLO"],
    },
    name="first_op_example",
)
second_op_example = k8s_job_op.configured(
    {
        "image": "busybox",
        "command": ["/bin/sh", "-c"],
        "args": ["echo GOODBYE"],
    },
    name="second_op_example",
)

@job
def full_job_example():
    second_op_example(first_op_example())
# end_marker
# fmt: on


def test_k8s_job_op_example_loads():
    assert full_job_example


@mock.patch("dagster_k8s.ops.k8s_job_op.execute_k8s_job")
def test_k8s_job_op_retry_on_preemption_config_true(mock_execute_k8s_job):
    op_config_true = {
        "image": "busybox",
        "command": ["echo", "hello"],
        "retry_on_preemption": True,
    }
    
    # Need to use the underlying op definition for direct invocation via context
    op_def = k8s_job_op
    
    # Build a context
    context = build_op_context(op_config=op_config_true)

    op_def(context)

    mock_execute_k8s_job.assert_called_once()
    call_args = mock_execute_k8s_job.call_args[1] # Get kwargs
    assert call_args.get("retry_on_preemption") is True
    assert call_args.get("merge_behavior") == K8sConfigMergeBehavior.DEEP # Default
    # Ensure other configs are passed
    assert call_args.get("image") == "busybox"
    assert call_args.get("command") == ["echo", "hello"]


@mock.patch("dagster_k8s.ops.k8s_job_op.execute_k8s_job")
def test_k8s_job_op_retry_on_preemption_config_false(mock_execute_k8s_job):
    op_config_false = {
        "image": "busybox",
        "command": ["echo", "hello"],
        "retry_on_preemption": False,
    }
    op_def = k8s_job_op
    context = build_op_context(op_config=op_config_false)
    op_def(context)

    mock_execute_k8s_job.assert_called_once()
    call_args = mock_execute_k8s_job.call_args[1]
    assert call_args.get("retry_on_preemption") is False
    assert call_args.get("image") == "busybox"


@mock.patch("dagster_k8s.ops.k8s_job_op.execute_k8s_job")
def test_k8s_job_op_retry_on_preemption_config_default(mock_execute_k8s_job):
    # Test default value (should be False)
    op_config_default = {
        "image": "busybox",
        "command": ["echo", "hello"],
        # retry_on_preemption is omitted
    }
    op_def = k8s_job_op
    context = build_op_context(op_config=op_config_default)
    op_def(context)
    
    mock_execute_k8s_job.assert_called_once()
    call_args = mock_execute_k8s_job.call_args[1]
    # The pop in the op itself defaults to False if not found
    assert call_args.get("retry_on_preemption") is False
    assert call_args.get("image") == "busybox"

@mock.patch("dagster_k8s.ops.k8s_job_op.execute_k8s_job")
def test_k8s_job_op_merge_behavior_custom(mock_execute_k8s_job):
    op_config_merge = {
        "image": "busybox",
        "command": ["echo", "hello"],
        "merge_behavior": "SHALLOW", # K8sConfigMergeBehavior.SHALLOW.value
    }
    op_def = k8s_job_op
    context = build_op_context(op_config=op_config_merge)
    op_def(context)
    
    mock_execute_k8s_job.assert_called_once()
    call_args = mock_execute_k8s_job.call_args[1]
    assert call_args.get("merge_behavior") == K8sConfigMergeBehavior.SHALLOW
    assert call_args.get("retry_on_preemption") is False # Default
