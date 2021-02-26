# start_mypipeline
from dagster import ModeDefinition, pipeline, repository
from dagster.core.storage.memoizable_io_manager import versioned_filesystem_io_manager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from memoized_development.solids.dog import emit_dog
from memoized_development.solids.sentence import emit_sentence
from memoized_development.solids.tree import emit_tree


@pipeline(
    mode_defs=[
        ModeDefinition("memoized", resource_defs={"io_manager": versioned_filesystem_io_manager}),
    ],
    tags={MEMOIZED_RUN_TAG: "true"},
)
def my_pipeline():
    return emit_sentence(emit_dog(), emit_tree())


# end_mypipeline


@repository
def memoized_development():
    return [my_pipeline]
