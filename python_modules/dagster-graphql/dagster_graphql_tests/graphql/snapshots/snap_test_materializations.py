# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestMaterializations.test_materializations[in_memory_instance_in_process_env] 1'] = [
    'PipelineStartEvent',
    'ExecutionStepStartEvent',
    'StepMaterializationEvent',
    'ExecutionStepOutputEvent',
    'ExecutionStepSuccessEvent',
    'PipelineSuccessEvent'
]

snapshots['TestMaterializations.test_materializations[sqlite_with_sync_run_launcher_in_process_env] 1'] = [
    'PipelineStartEvent',
    'ExecutionStepStartEvent',
    'StepMaterializationEvent',
    'ExecutionStepOutputEvent',
    'ExecutionStepSuccessEvent',
    'PipelineSuccessEvent'
]

snapshots['TestMaterializations.test_materializations[sqlite_with_cli_api_run_launcher_in_process_env] 1'] = [
    'PipelineStartEvent',
    'ExecutionStepStartEvent',
    'StepMaterializationEvent',
    'ExecutionStepOutputEvent',
    'ExecutionStepSuccessEvent',
    'PipelineSuccessEvent'
]
