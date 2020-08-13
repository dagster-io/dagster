import sys

from dagster import lambda_solid, pipeline, repository
from dagster.core.host_representation import PythonEnvRepositoryLocation, RepositoryLocationHandle
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.utils.hosted_user_process import recon_pipeline_from_origin


@lambda_solid
def the_solid():
    return 'yep'


@pipeline
def the_pipe():
    the_solid()


@repository
def the_repo():
    return [the_pipe]


def test_origin_id():
    host_location = PythonEnvRepositoryLocation(
        RepositoryLocationHandle.create_python_env_location(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable, python_file=__file__, attribute='the_repo'
            ),
            location_name='the_location',
        )
    )

    external_pipeline = host_location.get_repository('the_repo').get_full_external_pipeline(
        'the_pipe'
    )
    recon_pipeline = recon_pipeline_from_origin(external_pipeline.get_origin())

    assert external_pipeline.get_origin_id() == recon_pipeline.get_origin_id()
