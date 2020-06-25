import os

from dagster_graphql.client.mutations import handle_execute_plan_result, handle_execution_errors

from dagster import DagsterInstance, EventMetadataEntry, check, seven
from dagster.core.events import EngineEventData
from dagster.core.instance import InstanceRef
from dagster.serdes import serialize_dagster_namedtuple
from dagster.seven import JSONDecodeError

from .core_execution_loop import DELEGATE_MARKER


def create_docker_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name='execute_step_docker', **task_kwargs)
    def _execute_step_docker(
        _self,
        instance_ref_dict,
        step_keys,
        run_config,
        mode,
        repo_name,
        repo_location_name,
        run_id,
        docker_image,
        docker_registry,
        docker_username,
        docker_password,
    ):
        '''Run step execution in a Docker container.
        '''
        import docker.client
        from .executor_docker import CeleryDockerExecutor

        instance_ref = InstanceRef.from_dict(instance_ref_dict)
        instance = DagsterInstance.from_ref(instance_ref)
        pipeline_run = instance.get_run_by_id(run_id)
        check.invariant(pipeline_run, 'Could not load run {}'.format(run_id))

        step_keys_str = ", ".join(step_keys)

        variables = {
            'executionParams': {
                'runConfigData': run_config,
                'mode': mode,
                'selector': {
                    'repositoryLocationName': repo_location_name,
                    'repositoryName': repo_name,
                    'pipelineName': pipeline_run.pipeline_name,
                },
                'executionMetadata': {'runId': run_id},
                'stepKeys': step_keys,
            }
        }

        command = 'dagster-graphql -v \'{variables}\' -p executePlan'.format(
            variables=seven.json.dumps(variables)
        )

        client = docker.client.from_env()

        if docker_username:
            client.login(
                registry=docker_registry, username=docker_username, password=docker_password,
            )

        # Post event for starting execution
        engine_event = instance.report_engine_event(
            'Executing steps {} in Docker container {}'.format(step_keys_str, docker_image),
            pipeline_run,
            EngineEventData(
                [
                    EventMetadataEntry.text(step_keys_str, 'Step keys'),
                    EventMetadataEntry.text(docker_image, 'Job image'),
                ],
                marker_end=DELEGATE_MARKER,
            ),
            CeleryDockerExecutor,
            step_key=step_keys[0],
        )

        events = [engine_event]

        docker_response = client.containers.run(
            docker_image,
            command=command,
            detach=False,
            auto_remove=True,
            # pass through this worker's environment for things like AWS creds etc.
            environment=dict(os.environ),
        )

        try:
            res = seven.json.loads(docker_response)

        except JSONDecodeError:
            fail_event = instance.report_engine_event(
                'Failed to run steps {} in Docker container {}'.format(step_keys_str, docker_image),
                pipeline_run,
                EngineEventData(
                    [
                        EventMetadataEntry.text(step_keys_str, 'Step keys'),
                        EventMetadataEntry.text(docker_image, 'Job image'),
                        EventMetadataEntry.text(docker_response, 'Docker Response'),
                    ],
                    marker_end=DELEGATE_MARKER,
                ),
                CeleryDockerExecutor,
                step_key=step_keys[0],
            )

            events.append(fail_event)

        else:
            handle_execution_errors(res, 'executePlan')
            step_events = handle_execute_plan_result(res)

        events += step_events

        serialized_events = [serialize_dagster_namedtuple(event) for event in events]
        return serialized_events

    return _execute_step_docker
