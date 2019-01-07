# pylint: disable=W0622,W0614,W0401
from dagster import PipelineDefinition, RepositoryDefinition, lambda_solid


@lambda_solid
def hello_world():
    pass


def define_part_six_pipeline():
    return PipelineDefinition(name='part_six_pipeline', solids=[hello_world])


def define_part_six_repo():
    return RepositoryDefinition(
        name='part_six_repo', pipeline_dict={'part_six_pipeline': define_part_six_pipeline}
    )


def test_part_six_repo():
    assert define_part_six_repo().get_pipeline('part_six_pipeline').name == 'part_six_pipeline'
