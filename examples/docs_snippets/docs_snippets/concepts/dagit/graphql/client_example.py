# isort: skip_file
# pylint: disable=W0404
# start_setup_marker
from dagster_graphql import DagsterGraphQLClient

client = DagsterGraphQLClient("localhost", port_number=3000)

# end_setup_marker

RUN_ID = "foo"
REPO_NAME = "bar"
JOB_NAME = "baz"
REPO_NAME = "quux"
REPO_LOCATION_NAME = "corge"


def do_something_on_success(some_arg=None):  # pylint: disable=W0613
    pass


def do_something_else():
    pass


def do_something_with_exc(some_exception):  # pylint: disable=W0613
    pass


# start_submit_marker_default
from dagster_graphql import DagsterGraphQLClientError

try:
    new_run_id: str = client.submit_job_execution(
        JOB_NAME,
        repository_location_name=REPO_LOCATION_NAME,
        repository_name=REPO_NAME,
        run_config={},
    )
    do_something_on_success(new_run_id)
except DagsterGraphQLClientError as exc:
    do_something_with_exc(exc)
    raise exc
# end_submit_marker_default


# start_submit_marker_job_name_only
from dagster_graphql import DagsterGraphQLClientError

try:
    new_run_id: str = client.submit_job_execution(
        JOB_NAME,
        run_config={},
    )
    do_something_on_success(new_run_id)
except DagsterGraphQLClientError as exc:
    do_something_with_exc(exc)
    raise exc
# end_submit_marker_job_name_only


# start_run_status_marker
from dagster_graphql import DagsterGraphQLClientError
from dagster import PipelineRunStatus

try:
    status: PipelineRunStatus = client.get_run_status(RUN_ID)
    if status == PipelineRunStatus.SUCCESS:
        do_something_on_success()
    else:
        do_something_else()
except DagsterGraphQLClientError as exc:
    do_something_with_exc(exc)
    raise exc
# end_run_status_marker


# start_reload_repo_location_marker
from dagster_graphql import (
    ReloadRepositoryLocationInfo,
    ReloadRepositoryLocationStatus,
)

reload_info: ReloadRepositoryLocationInfo = client.reload_repository_location(REPO_NAME)
if reload_info.status == ReloadRepositoryLocationStatus.SUCCESS:
    do_something_on_success()
else:
    raise Exception(
        "Repository location reload failed because of a "
        f"{reload_info.failure_type} error: {reload_info.message}"
    )
# end_reload_repo_location_marker

# start_shutdown_repo_location_marker
from dagster_graphql import (
    ShutdownRepositoryLocationInfo,
    ShutdownRepositoryLocationStatus,
)

shutdown_info: ShutdownRepositoryLocationInfo = client.shutdown_repository_location(
    REPO_NAME
)
if shutdown_info.status == ShutdownRepositoryLocationStatus.SUCCESS:
    do_something_on_success()
else:
    raise Exception(f"Repository location shutdown failed: {shutdown_info.message}")
# end_shutdown_repo_location_marker
