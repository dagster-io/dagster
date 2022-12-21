# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot

snapshots = Snapshot()

snapshots[
    "TestCapturedLogs.test_captured_logs_subscription_graphql[postgres_with_default_run_launcher_deployed_grpc_env] 1"
] = [
    GenericRepr(
        "ExecutionResult(data={'capturedLogs': {'stdout': 'HELLO WORLD\\n', 'stderr': '2022-11-10"
        " 16:44:58 -0600 - dagster - DEBUG - spew_pipeline - abfbcdd1-1083-46a6-a646-d361f4f4fabf -"
        " 97337 - LOGS_CAPTURED - Started capturing logs in process (pid: 97337).\\n2022-11-10"
        " 16:44:58 -0600 - dagster - DEBUG - spew_pipeline - abfbcdd1-1083-46a6-a646-d361f4f4fabf -"
        ' 97337 - spew - STEP_START - Started execution of step "spew".\\n2022-11-10 16:44:58'
        " -0600 - dagster - DEBUG - spew_pipeline - abfbcdd1-1083-46a6-a646-d361f4f4fabf - 97337 -"
        ' spew - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check'
        " passed).\\n2022-11-10 16:44:58 -0600 - dagster - DEBUG - spew_pipeline -"
        " abfbcdd1-1083-46a6-a646-d361f4f4fabf - 97337 - spew - HANDLED_OUTPUT - Handled output"
        ' "result" using IO manager "io_manager"\\n2022-11-10 16:44:58 -0600 - dagster - DEBUG'
        " - spew_pipeline - abfbcdd1-1083-46a6-a646-d361f4f4fabf - 97337 - spew - STEP_SUCCESS -"
        " Finished execution of step \"spew\" in 15ms.\\n', 'cursor': '12:887'}}, errors=None)"
    )
]

snapshots[
    "TestCapturedLogs.test_captured_logs_subscription_graphql[postgres_with_default_run_launcher_managed_grpc_env] 1"
] = [
    GenericRepr(
        "ExecutionResult(data={'capturedLogs': {'stdout': 'HELLO WORLD\\n', 'stderr': '2022-11-10"
        " 16:44:45 -0600 - dagster - DEBUG - spew_pipeline - 25d287f2-51b6-4d5a-98a4-c261b68b8415 -"
        " 97284 - LOGS_CAPTURED - Started capturing logs in process (pid: 97284).\\n2022-11-10"
        " 16:44:45 -0600 - dagster - DEBUG - spew_pipeline - 25d287f2-51b6-4d5a-98a4-c261b68b8415 -"
        ' 97284 - spew - STEP_START - Started execution of step "spew".\\n2022-11-10 16:44:45'
        " -0600 - dagster - DEBUG - spew_pipeline - 25d287f2-51b6-4d5a-98a4-c261b68b8415 - 97284 -"
        ' spew - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check'
        " passed).\\n2022-11-10 16:44:45 -0600 - dagster - DEBUG - spew_pipeline -"
        " 25d287f2-51b6-4d5a-98a4-c261b68b8415 - 97284 - spew - HANDLED_OUTPUT - Handled output"
        ' "result" using IO manager "io_manager"\\n2022-11-10 16:44:45 -0600 - dagster - DEBUG'
        " - spew_pipeline - 25d287f2-51b6-4d5a-98a4-c261b68b8415 - 97284 - spew - STEP_SUCCESS -"
        " Finished execution of step \"spew\" in 18ms.\\n', 'cursor': '12:887'}}, errors=None)"
    )
]

snapshots[
    "TestCapturedLogs.test_captured_logs_subscription_graphql[sqlite_with_default_run_launcher_deployed_grpc_env] 1"
] = [
    GenericRepr(
        "ExecutionResult(data={'capturedLogs': {'stdout': 'HELLO WORLD\\n', 'stderr': '2022-11-10"
        " 16:44:36 -0600 - dagster - DEBUG - spew_pipeline - 2ea8458c-bd00-421d-b969-871a381d3a88 -"
        " 97244 - LOGS_CAPTURED - Started capturing logs in process (pid: 97244).\\n2022-11-10"
        " 16:44:36 -0600 - dagster - DEBUG - spew_pipeline - 2ea8458c-bd00-421d-b969-871a381d3a88 -"
        ' 97244 - spew - STEP_START - Started execution of step "spew".\\n2022-11-10 16:44:36'
        " -0600 - dagster - DEBUG - spew_pipeline - 2ea8458c-bd00-421d-b969-871a381d3a88 - 97244 -"
        ' spew - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check'
        " passed).\\n2022-11-10 16:44:36 -0600 - dagster - DEBUG - spew_pipeline -"
        " 2ea8458c-bd00-421d-b969-871a381d3a88 - 97244 - spew - HANDLED_OUTPUT - Handled output"
        ' "result" using IO manager "io_manager"\\n2022-11-10 16:44:36 -0600 - dagster - DEBUG'
        " - spew_pipeline - 2ea8458c-bd00-421d-b969-871a381d3a88 - 97244 - spew - STEP_SUCCESS -"
        " Finished execution of step \"spew\" in 11ms.\\n', 'cursor': '12:887'}}, errors=None)"
    )
]

snapshots[
    "TestCapturedLogs.test_captured_logs_subscription_graphql[sqlite_with_default_run_launcher_managed_grpc_env] 1"
] = [
    GenericRepr(
        "ExecutionResult(data={'capturedLogs': {'stdout': 'HELLO WORLD\\n', 'stderr': '2022-11-10"
        " 16:44:32 -0600 - dagster - DEBUG - spew_pipeline - 86d26c77-2b71-4646-a791-b217a741553c -"
        " 97229 - LOGS_CAPTURED - Started capturing logs in process (pid: 97229).\\n2022-11-10"
        " 16:44:32 -0600 - dagster - DEBUG - spew_pipeline - 86d26c77-2b71-4646-a791-b217a741553c -"
        ' 97229 - spew - STEP_START - Started execution of step "spew".\\n2022-11-10 16:44:32'
        " -0600 - dagster - DEBUG - spew_pipeline - 86d26c77-2b71-4646-a791-b217a741553c - 97229 -"
        ' spew - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check'
        " passed).\\n2022-11-10 16:44:32 -0600 - dagster - DEBUG - spew_pipeline -"
        " 86d26c77-2b71-4646-a791-b217a741553c - 97229 - spew - HANDLED_OUTPUT - Handled output"
        ' "result" using IO manager "io_manager"\\n2022-11-10 16:44:32 -0600 - dagster - DEBUG'
        " - spew_pipeline - 86d26c77-2b71-4646-a791-b217a741553c - 97229 - spew - STEP_SUCCESS -"
        " Finished execution of step \"spew\" in 10ms.\\n', 'cursor': '12:887'}}, errors=None)"
    )
]

snapshots[
    "TestCapturedLogs.test_get_captured_logs_over_graphql[postgres_with_default_run_launcher_deployed_grpc_env] 1"
] = """HELLO WORLD
"""

snapshots[
    "TestCapturedLogs.test_get_captured_logs_over_graphql[postgres_with_default_run_launcher_managed_grpc_env] 1"
] = """HELLO WORLD
"""

snapshots[
    "TestCapturedLogs.test_get_captured_logs_over_graphql[sqlite_with_default_run_launcher_deployed_grpc_env] 1"
] = """HELLO WORLD
"""

snapshots[
    "TestCapturedLogs.test_get_captured_logs_over_graphql[sqlite_with_default_run_launcher_managed_grpc_env] 1"
] = """HELLO WORLD
"""

snapshots[
    "TestComputeLogs.test_compute_logs_subscription_graphql[postgres_with_default_run_launcher_deployed_grpc_env] 1"
] = [
    """HELLO WORLD
"""
]

snapshots[
    "TestComputeLogs.test_compute_logs_subscription_graphql[postgres_with_default_run_launcher_managed_grpc_env] 1"
] = [
    """HELLO WORLD
"""
]

snapshots[
    "TestComputeLogs.test_compute_logs_subscription_graphql[sqlite_with_default_run_launcher_deployed_grpc_env] 1"
] = [
    """HELLO WORLD
"""
]

snapshots[
    "TestComputeLogs.test_compute_logs_subscription_graphql[sqlite_with_default_run_launcher_managed_grpc_env] 1"
] = [
    """HELLO WORLD
"""
]

snapshots[
    "TestComputeLogs.test_get_compute_logs_over_graphql[postgres_with_default_run_launcher_deployed_grpc_env] 1"
] = """HELLO WORLD
"""

snapshots[
    "TestComputeLogs.test_get_compute_logs_over_graphql[postgres_with_default_run_launcher_managed_grpc_env] 1"
] = """HELLO WORLD
"""

snapshots[
    "TestComputeLogs.test_get_compute_logs_over_graphql[sqlite_with_default_run_launcher_deployed_grpc_env] 1"
] = """HELLO WORLD
"""

snapshots[
    "TestComputeLogs.test_get_compute_logs_over_graphql[sqlite_with_default_run_launcher_managed_grpc_env] 1"
] = """HELLO WORLD
"""
