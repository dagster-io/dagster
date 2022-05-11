from contextlib import contextmanager

from dagster_graphql.schema import create_schema
from graphql import graphql

import dagster._check as check
from dagster.core.instance import DagsterInstance
from dagster.core.workspace import WorkspaceProcessContext
from dagster.core.workspace.load_target import PythonFileTarget


def main_repo_location_name():
    return "test_location"


def main_repo_name():
    return "test_repo"


def execute_dagster_graphql(context, query, variables=None):
    result = graphql(
        create_schema(),
        query,
        context_value=context,
        variable_values=variables,
        allow_subscriptions=True,
        return_promise=False,
    )

    # has to check attr because in subscription case it returns AnonymousObservable
    if hasattr(result, "errors") and result.errors:
        first_error = result.errors[0]
        if hasattr(first_error, "original_error") and first_error.original_error:
            raise result.errors[0].original_error

        raise result.errors[0]

    return result


def execute_dagster_graphql_and_finish_runs(context, query, variables=None):
    result = execute_dagster_graphql(context, query, variables)
    context.instance.run_launcher.join()
    return result


@contextmanager
def define_out_of_process_context(python_file, fn_name, instance):
    check.inst_param(instance, "instance", DagsterInstance)

    with define_out_of_process_workspace(
        python_file, fn_name, instance
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


def define_out_of_process_workspace(python_file, fn_name, instance):
    return WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=python_file,
            attribute=fn_name,
            working_directory=None,
            location_name=main_repo_location_name(),
        ),
        version="",
    )


def infer_repository(graphql_context):
    if len(graphql_context.repository_locations) == 1:
        # This is to account for having a single in process repository
        repository_location = graphql_context.repository_locations[0]
        repositories = repository_location.get_repositories()
        assert len(repositories) == 1
        return next(iter(repositories.values()))

    repository_location = graphql_context.get_repository_location("test")
    return repository_location.get_repository("test_repo")


def infer_repository_selector(graphql_context):
    if len(graphql_context.repository_locations) == 1:
        # This is to account for having a single in process repository
        repository_location = graphql_context.repository_locations[0]
        repositories = repository_location.get_repositories()
        assert len(repositories) == 1
        repository = next(iter(repositories.values()))
    else:
        repository_location = graphql_context.get_repository_location("test")
        repository = repository_location.get_repository("test_repo")

    return {
        "repositoryLocationName": repository_location.name,
        "repositoryName": repository.name,
    }


def infer_job_or_pipeline_selector(
    graphql_context,
    pipeline_name,
    solid_selection=None,
    asset_selection=None,
):
    selector = infer_repository_selector(graphql_context)
    selector.update(
        {
            "pipelineName": pipeline_name,
            "solidSelection": solid_selection,
            "assetSelection": asset_selection,
        }
    )
    return selector


def infer_pipeline_selector(
    graphql_context,
    pipeline_name,
    solid_selection=None,
):
    selector = infer_repository_selector(graphql_context)
    selector.update(
        {
            "pipelineName": pipeline_name,
            "solidSelection": solid_selection,
        }
    )
    return selector


def infer_schedule_selector(graphql_context, schedule_name):
    selector = infer_repository_selector(graphql_context)
    selector.update({"scheduleName": schedule_name})
    return selector


def infer_sensor_selector(graphql_context, sensor_name):
    selector = infer_repository_selector(graphql_context)
    selector.update({"sensorName": sensor_name})
    return selector


def infer_instigation_selector(graphql_context, name):
    selector = infer_repository_selector(graphql_context)
    selector.update({"name": name})
    return selector
