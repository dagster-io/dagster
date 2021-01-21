# start_repo_marker_0
from dagster import PresetDefinition, pipeline, repository, solid


@solid(tags={"metadata": "some_metadata"})
def get_tag(context):
    metadata = context.solid_def.tags.get("metadata")
    context.log.info("solid has tag: {}".format(metadata))
    owner = context.pipeline_run.tags.get("owner")
    context.log.info("owner is {}".format(owner))
    return metadata, owner


@pipeline(
    tags={"owner": "ml_team", "source": "pipeline"},
    preset_defs=[PresetDefinition("tag_preset", tags={"oncall": "ml_team", "source": "preset"})],
)
def tags_pipeline():
    get_tag()


@repository
def pipeline_tags_example():
    return [tags_pipeline]


# end_repo_marker_0
