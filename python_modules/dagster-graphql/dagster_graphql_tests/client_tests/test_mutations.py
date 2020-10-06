import re

import pytest
from dagster_graphql.client.mutations import (
    DagsterGraphQLClientError,
    execute_execute_plan_mutation,
    execute_execute_plan_mutation_raw,
)

from dagster import file_relative_path
from dagster.cli.workspace.cli_target import PythonFileTarget, workspace_from_load_target
from dagster.core.definitions.reconstructable import (
    ReconstructablePipeline,
    get_ephemeral_repository_name,
)
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.core.instance import DagsterInstance
from dagster.utils.hosted_user_process import create_in_process_ephemeral_workspace

EXPECTED_EVENTS = {
    ("STEP_INPUT", "sleeper.compute"),
    ("STEP_INPUT", "sleeper_2.compute"),
    ("STEP_INPUT", "sleeper_3.compute"),
    ("STEP_INPUT", "sleeper_4.compute"),
    ("STEP_INPUT", "total.compute"),
    ("STEP_OUTPUT", "giver.compute"),
    ("STEP_OUTPUT", "sleeper.compute"),
    ("STEP_OUTPUT", "sleeper_2.compute"),
    ("STEP_OUTPUT", "sleeper_3.compute"),
    ("STEP_OUTPUT", "sleeper_4.compute"),
    ("STEP_OUTPUT", "total.compute"),
    ("STEP_START", "giver.compute"),
    ("STEP_START", "sleeper.compute"),
    ("STEP_START", "sleeper_2.compute"),
    ("STEP_START", "sleeper_3.compute"),
    ("STEP_START", "sleeper_4.compute"),
    ("STEP_START", "total.compute"),
    ("STEP_SUCCESS", "giver.compute"),
    ("STEP_SUCCESS", "sleeper.compute"),
    ("STEP_SUCCESS", "sleeper_2.compute"),
    ("STEP_SUCCESS", "sleeper_3.compute"),
    ("STEP_SUCCESS", "sleeper_4.compute"),
    ("STEP_SUCCESS", "total.compute"),
}


def load_sleepy_workspace(instance):
    return workspace_from_load_target(
        PythonFileTarget(
            file_relative_path(__file__, "sleepy.py"), "sleepy_pipeline", working_directory=None
        ),
        instance,
    )


def sleepy_recon_pipeline():
    return ReconstructablePipeline.for_file(
        file_relative_path(__file__, "sleepy.py"), "sleepy_pipeline"
    )


def test_execute_execute_plan_mutation_out_of_process_fails():
    pipeline_name = "sleepy_pipeline"
    instance = DagsterInstance.local_temp()

    pipeline = sleepy_recon_pipeline()
    workspace = load_sleepy_workspace(instance)
    pipeline_run = instance.create_run_for_pipeline(pipeline_def=pipeline.get_definition())
    variables = {
        "executionParams": {
            "runConfigData": {},
            "mode": "default",
            "selector": {
                "repositoryLocationName": get_ephemeral_repository_name(pipeline_name),
                "repositoryName": get_ephemeral_repository_name(pipeline_name),
                "pipelineName": pipeline_name,
            },
            "executionMetadata": {"runId": pipeline_run.run_id},
        }
    }
    with pytest.raises(
        DagsterGraphQLClientError,
        match=re.escape("execute_plan is not supported for out-of-process repository locations"),
    ):
        execute_execute_plan_mutation(workspace, variables, instance_ref=instance.get_ref())


def test_execute_execute_plan_mutation():
    pipeline_name = "sleepy_pipeline"
    instance = DagsterInstance.local_temp()

    pipeline = sleepy_recon_pipeline()
    workspace = create_in_process_ephemeral_workspace(pointer=pipeline.repository.pointer)
    pipeline_run = instance.create_run_for_pipeline(pipeline_def=pipeline.get_definition())
    variables = {
        "executionParams": {
            "runConfigData": {},
            "mode": "default",
            "selector": {
                "repositoryLocationName": IN_PROCESS_NAME,
                "repositoryName": get_ephemeral_repository_name(pipeline_name),
                "pipelineName": pipeline_name,
            },
            "executionMetadata": {"runId": pipeline_run.run_id},
        }
    }
    result = execute_execute_plan_mutation(workspace, variables, instance_ref=instance.get_ref())
    seen_events = set()
    for event in result:
        seen_events.add((event.event_type_value, event.step_key))

    assert seen_events == EXPECTED_EVENTS


def test_execute_execute_plan_mutation_raw():
    pipeline_name = "sleepy_pipeline"
    pipeline = sleepy_recon_pipeline()
    instance = DagsterInstance.local_temp()

    workspace = create_in_process_ephemeral_workspace(pointer=pipeline.repository.pointer)

    pipeline_run = instance.create_run_for_pipeline(pipeline_def=pipeline.get_definition())
    variables = {
        "executionParams": {
            "runConfigData": {},
            "mode": "default",
            "selector": {
                "repositoryLocationName": IN_PROCESS_NAME,
                "repositoryName": get_ephemeral_repository_name(pipeline_name),
                "pipelineName": pipeline_name,
            },
            "executionMetadata": {"runId": pipeline_run.run_id},
        }
    }
    result = execute_execute_plan_mutation_raw(
        workspace, variables, instance_ref=instance.get_ref()
    )
    seen_events = set()
    for event in result:
        seen_events.add((event.dagster_event.event_type_value, event.step_key))

    assert seen_events == EXPECTED_EVENTS
