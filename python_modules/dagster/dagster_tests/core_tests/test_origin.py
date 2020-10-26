import sys

import pytest
from dagster import lambda_solid, pipeline, repository
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    PythonEnvRepositoryLocationOrigin,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.host_representation.handle import UserProcessApi
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.utils.hosted_user_process import recon_pipeline_from_origin


@lambda_solid
def the_solid():
    return "yep"


@pipeline
def the_pipe():
    the_solid()


@repository
def the_repo():
    return [the_pipe]


@pytest.mark.parametrize("user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC])
def test_origin_id(user_process_api):

    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, attribute="the_repo"
    )
    location_name = "the_location"

    origin = (
        ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin, location_name)
        if user_process_api == UserProcessApi.GRPC
        else PythonEnvRepositoryLocationOrigin(loadable_target_origin, location_name)
    )

    with RepositoryLocationHandle.create_from_repository_location_origin(origin) as handle:
        host_location = RepositoryLocation.from_handle(handle)

        external_pipeline = host_location.get_repository("the_repo").get_full_external_pipeline(
            "the_pipe"
        )
        recon_pipeline = recon_pipeline_from_origin(external_pipeline.get_origin())

        assert external_pipeline.get_origin_id() == recon_pipeline.get_origin_id()
