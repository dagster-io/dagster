from dagster import pipeline, repository, solid


@solid
def get_tag(context):
    owner = context.pipeline_run.tags.get('owner')
    context.log.info('owner is {}'.format(owner))
    return


@pipeline(tags={'owner': 'ml_team'})
def tags_pipeline():
    get_tag()


@repository
def pipeline_tags_example():
    return [tags_pipeline]
