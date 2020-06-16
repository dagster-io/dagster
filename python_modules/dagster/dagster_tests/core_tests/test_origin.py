from dagster import lambda_solid, pipeline, repository
from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import PythonEnvRepositoryLocation, RepositoryLocationHandle
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
        RepositoryLocationHandle.create_out_of_process_location(
            location_name='the_location',
            repository_code_pointer_dict={'the_repo': FileCodePointer(__file__, 'the_repo'),},
        )
    )

    external_pipeline = host_location.get_repository('the_repo').get_full_external_pipeline(
        'the_pipe'
    )
    recon_pipeline = recon_pipeline_from_origin(external_pipeline.get_origin())

    assert external_pipeline.get_origin_id() == recon_pipeline.get_origin_id()
