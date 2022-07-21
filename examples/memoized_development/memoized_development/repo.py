# start_mypipeline
from memoized_development.solids.dog import emit_dog
from memoized_development.solids.sentence import emit_sentence
from memoized_development.solids.tree import emit_tree

from dagster import ModeDefinition, repository
from dagster._legacy import pipeline
from dagster._core.storage.memoizable_io_manager import versioned_filesystem_io_manager
from dagster._core.storage.tags import MEMOIZED_RUN_TAG


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
