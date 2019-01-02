from dagster import lambda_solid, PipelineDefinition, RepositoryDefinition


@lambda_solid
def hello_world():
    pass


def define_part_six_pipeline():
    return PipelineDefinition(name='part_six', solids=[hello_world])


def define_part_six_repo():
    return RepositoryDefinition(
        name='part_six_repo', pipeline_dict={'part_six': define_part_six_pipeline}
    )
