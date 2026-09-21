import pytest
from dagster._utils.error import SerializableErrorInfo
from dagster_cloud.util.container_resources import (
    interpret_ecs_cpu_str_as_millicpus,
    interpret_ecs_mem_str_as_bytes,
    interpret_k8s_cpu_str_as_millicpus,
    interpret_k8s_mem_str_as_bytes,
)
from dagster_cloud.util.errors import remove_dagster_framework_lines_from_serializable_exc_info


def test_resource_limit_interpreters():
    for fn in [
        interpret_ecs_cpu_str_as_millicpus,
        interpret_ecs_mem_str_as_bytes,
        interpret_k8s_cpu_str_as_millicpus,
        interpret_k8s_mem_str_as_bytes,
    ]:
        assert fn(None) is None

    assert interpret_k8s_mem_str_as_bytes("1") == 1
    assert interpret_k8s_mem_str_as_bytes("1Mi") == 1024**2
    assert interpret_k8s_mem_str_as_bytes("1M") == 1000**2
    assert interpret_k8s_mem_str_as_bytes("1Gi") == 1024**3
    assert interpret_k8s_mem_str_as_bytes("1G") == 1000**3
    assert interpret_k8s_mem_str_as_bytes("1Ti") == 1024**4
    assert interpret_k8s_mem_str_as_bytes("1T") == 1000**4
    assert interpret_k8s_mem_str_as_bytes("1Pi") == 1024**5
    assert interpret_k8s_mem_str_as_bytes("1P") == 1000**5
    assert interpret_k8s_mem_str_as_bytes("1Ei") == 1024**6
    assert interpret_k8s_mem_str_as_bytes("1E") == 1000**6
    assert interpret_k8s_mem_str_as_bytes("1K") == 1000
    assert interpret_k8s_mem_str_as_bytes("1Ki") == 1024

    with pytest.raises(Exception):
        interpret_k8s_mem_str_as_bytes("1KB")

    assert interpret_k8s_cpu_str_as_millicpus("10") == 10000
    assert interpret_k8s_cpu_str_as_millicpus("1m") == 1
    assert interpret_k8s_cpu_str_as_millicpus("0.1") == 100

    with pytest.raises(Exception):
        interpret_k8s_cpu_str_as_millicpus("1K")

    assert interpret_ecs_mem_str_as_bytes("1") == 1024**2
    assert interpret_ecs_mem_str_as_bytes("1GB") == 1024**3

    with pytest.raises(Exception):
        interpret_ecs_mem_str_as_bytes("1Gi")

    assert interpret_ecs_cpu_str_as_millicpus("10") == 10
    assert interpret_ecs_cpu_str_as_millicpus("1") == 1

    with pytest.raises(Exception):
        interpret_ecs_cpu_str_as_millicpus("1m")

    with pytest.raises(Exception):
        interpret_ecs_cpu_str_as_millicpus("0.1")

    for test_str in [
        "0.25vcpu",
        "0.25VCPU",
        "0.25vCPU",
        "0.25VCpu",
        "0.25vCpu",
        "0.25 vcpu",
        "0.25 VCPU",
        "0.25 vCPU",
        "0.25 VCpu",
        "0.25 vCpu",
    ]:
        assert interpret_ecs_cpu_str_as_millicpus(test_str) == 250


from dagster import deserialize_value, op

SERIALIZED_PROD_ERROR_WITH_FRAMEWORK_LINES = """{"__class__": "SerializableErrorInfo", "cause": null, "cls_name": "Exception", "context": {"__class__": "SerializableErrorInfo", "cause": null, "cls_name": "Exception", "context": null, "message": "Exception: Sling command failed:\\n[]\\n", "stack": ["  File \\"/usr/local/lib/python3.11/site-packages/sling/__init__.py\\", line 452, in _run\\n    for line in _exec_cmd(cmd, env=env, stdin=stdin):\\n", "  File \\"/usr/local/lib/python3.11/site-packages/sling/__init__.py\\", line 520, in _exec_cmd\\n    raise Exception(f'Sling command failed:\\\\n{lines}')\\n"]}, "message": "Exception: \\n\\u001b[90m7:40PM\\u001b[0m \\u001b[32mINF\\u001b[0m Sling Replication [1 streams] | CLOUD_PRODUCTION_MAIN -> SLING_DB_MAIN\\n\\u001b[90m7:40PM\\u001b[0m \\u001b[32mINF\\u001b[0m [1 / 1] running stream public.event_logs_view\\n\\u001b[90m7:40PM\\u001b[0m \\u001b[32mINF\\u001b[0m connecting to source database (postgres)\\n\\u001b[90m7:40PM\\u001b[0m \\u001b[32mINF\\u001b[0m \\u001b[31mexecution failed\\u001b[0m\\n\\n\\u001b[31mfatal:\\n~ failure running replication (see docs @ https://docs.slingdata.io/sling-cli)\\n--------------------------- public.event_logs_view ---------------------------\\n~ could not connect to database\\npq: canceling statement due to conflict with recovery\\u001b[0m\\n\\u001b[90m7:40PM\\u001b[0m \\u001b[32mINF\\u001b[0m \\u001b[31m~ could not connect to database\\npq: canceling statement due to conflict with recovery\\u001b[0m\\n\\n\\u001b[35mPerhaps adjusting the `max_standby_archive_delay` and `max_standby_streaming_delay` settings in the source PG Database could help. See https://stackoverflow.com/questions/14592436/postgresql-error-canceling-statement-due-to-conflict-with-recovery\\u001b[0m\\n\\n\\u001b[90m7:40PM\\u001b[0m \\u001b[32mINF\\u001b[0m Sling Replication Completed in 0s | CLOUD_PRODUCTION_MAIN -> SLING_DB_MAIN | \\u001b[32m0 Successes\\u001b[0m | \\u001b[31m1 Failures\\u001b[0m\\n\\nSling command failed:\\n[]\\n", "stack": ["  File \\"/usr/local/lib/python3.11/site-packages/dagster/_core/execution/plan/utils.py\\", line 54, in op_execution_error_boundary\\n    yield\\n", "  File \\"/usr/local/lib/python3.11/site-packages/dagster/_utils/__init__.py\\", line 482, in iterate_with_context\\n    next_output = next(iterator)\\n                  ^^^^^^^^^^^^^^\\n", "  File \\"/opt/python_modules/dagster-open-platform/dagster_open_platform/sling/assets.py\\", line 69, in cloud_product_main_event_log\\n    yield from embedded_elt.replicate(context=context).fetch_column_metadata().fetch_row_count()\\n", "  File \\"/usr/local/lib/python3.11/site-packages/dagster_sling/sling_event_iterator.py\\", line 189, in __next__\\n    return next(self._inner_iterator)\\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\\n", "  File \\"/usr/local/lib/python3.11/site-packages/dagster_sling/sling_event_iterator.py\\", line 229, in _fetch_row_count\\n    for event in self:\\n", "  File \\"/usr/local/lib/python3.11/site-packages/dagster_sling/sling_event_iterator.py\\", line 189, in __next__\\n    return next(self._inner_iterator)\\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\\n", "  File \\"/usr/local/lib/python3.11/site-packages/dagster_sling/sling_event_iterator.py\\", line 206, in _fetch_column_metadata\\n    for event in self:\\n", "  File \\"/usr/local/lib/python3.11/site-packages/dagster_sling/sling_event_iterator.py\\", line 189, in __next__\\n    return next(self._inner_iterator)\\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\\n", "  File \\"/usr/local/lib/python3.11/site-packages/dagster_sling/resources.py\\", line 388, in _replicate\\n    results = sling._run(  # noqa\\n              ^^^^^^^^^^^^^^^^^^^\\n", "  File \\"/usr/local/lib/python3.11/site-packages/sling/__init__.py\\", line 465, in _run\\n    raise Exception('\\\\n'.join(lines))\\n"]}"""

LOCAL_DEV_ERROR_WITH_FRAMEWORK_LINES = """{"__class__": "SerializableErrorInfo", "cause": null, "cls_name": "Exception", "context": {"__class__": "SerializableErrorInfo", "cause": null, "cls_name": "Exception", "context": null, "message": "Exception: INNER EXCEPTION\\n", "stack": ["  File \\"hi.py\\", line 21, in my_asset\\n    raise Exception(\\"INNER EXCEPTION\\")\\n"]}, "message": "Exception: OUTER EXCEPTION\\n", "stack": ["  File \\"/Users/dgibson/dagster/python_modules/dagster/dagster/_core/execution/plan/utils.py\\", line 54, in op_execution_error_boundary\\n    yield\\n", "  File \\"/Users/dgibson/dagster/python_modules/dagster/dagster/_utils/__init__.py\\", line 490, in iterate_with_context\\n    next_output = next(iterator)\\n", "  File \\"/Users/dgibson/dagster/python_modules/dagster/dagster/_core/execution/plan/compute_generator.py\\", line 140, in _coerce_op_compute_fn_to_iterator\\n    result = invoke_compute_fn(\\n", "  File \\"/Users/dgibson/dagster/python_modules/dagster/dagster/_core/execution/plan/compute_generator.py\\", line 128, in invoke_compute_fn\\n    return fn(context, **args_to_pass) if context_arg_provided else fn(**args_to_pass)\\n", "  File \\"hi.py\\", line 23, in my_asset\\n    raise Exception(\\"OUTER EXCEPTION\\")\\n"]}"""


def _helper_fn():
    raise Exception("Inner Exception")


@op
def my_op():
    try:
        _helper_fn()
    except:
        raise Exception("Outer exception")


def test_remove_dagster_framework_lines_from_prod_stack_trace(snapshot):
    # Snapshotting a constant looks a little pointless, but shows the before and after
    # more clearly in the snapshot file
    snapshot.assert_match(
        deserialize_value(SERIALIZED_PROD_ERROR_WITH_FRAMEWORK_LINES, SerializableErrorInfo)
    )

    serializable_error = deserialize_value(
        SERIALIZED_PROD_ERROR_WITH_FRAMEWORK_LINES, SerializableErrorInfo
    )

    removed_dagster_framework_error = remove_dagster_framework_lines_from_serializable_exc_info(
        serializable_error
    )

    snapshot.assert_match(removed_dagster_framework_error)


def test_remove_dagster_framework_lines_from_local_dev_stack_trace(snapshot):
    snapshot.assert_match(
        deserialize_value(LOCAL_DEV_ERROR_WITH_FRAMEWORK_LINES, SerializableErrorInfo)
    )

    serializable_error = deserialize_value(
        LOCAL_DEV_ERROR_WITH_FRAMEWORK_LINES, SerializableErrorInfo
    )

    removed_dagster_framework_error = remove_dagster_framework_lines_from_serializable_exc_info(
        serializable_error
    )

    snapshot.assert_match(removed_dagster_framework_error)
