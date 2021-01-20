# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestMaterializations.test_materializations[in_memory_instance_in_process_env] 1"] = [
    "PipelineStartingEvent",
    "PipelineStartEvent",
    "ExecutionStepStartEvent",
    "StepMaterializationEvent",
    "ExecutionStepOutputEvent",
    "HandledOutputEvent",
    "ExecutionStepSuccessEvent",
    "PipelineSuccessEvent",
]

snapshots[
    "TestMaterializations.test_materializations[sqlite_with_default_run_launcher_deployed_grpc_env] 1"
] = [
    "PipelineStartingEvent",
    "PipelineStartEvent",
    "ExecutionStepStartEvent",
    "StepMaterializationEvent",
    "ExecutionStepOutputEvent",
    "HandledOutputEvent",
    "ExecutionStepSuccessEvent",
    "PipelineSuccessEvent",
]

snapshots[
    "TestMaterializations.test_materializations[sqlite_with_default_run_launcher_managed_grpc_env] 1"
] = [
    "PipelineStartingEvent",
    "PipelineStartEvent",
    "ExecutionStepStartEvent",
    "StepMaterializationEvent",
    "ExecutionStepOutputEvent",
    "HandledOutputEvent",
    "ExecutionStepSuccessEvent",
    "PipelineSuccessEvent",
]

snapshots[
    "TestMaterializations.test_materializations[sqlite_with_sync_run_launcher_in_process_env] 1"
] = [
    "PipelineStartingEvent",
    "PipelineStartEvent",
    "ExecutionStepStartEvent",
    "StepMaterializationEvent",
    "ExecutionStepOutputEvent",
    "HandledOutputEvent",
    "ExecutionStepSuccessEvent",
    "PipelineSuccessEvent",
]
