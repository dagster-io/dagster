from dagster import RepositoryDefinition, pipeline, solid


@solid
def get_tag(context):
    owner = context.pipeline_run.tags.get('owner')
    context.log.info('owner is {}'.format(owner))
    return


@pipeline(tags={'owner': 'ml_team'})
def tags_pipeline():
    get_tag()


def define_repository():
    return RepositoryDefinition("pipeline_tags", pipeline_defs=[tags_pipeline])
