from dagster_graphql.test.preset_query import execute_preset_query
from dagster_graphql.test.utils import infer_repository

from .util import define_examples_context


def test_presets_on_examples(snapshot):
    context = define_examples_context()
    repository = infer_repository(context)
    pipeline_names = [pipeline_index.name for pipeline_index in repository.get_pipeline_indices()]
    for pipeline_name in sorted(pipeline_names):
        snapshot.assert_match(execute_preset_query(pipeline_name, context).data)
