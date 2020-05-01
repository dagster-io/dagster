from dagster_graphql.test.preset_query import execute_preset_query

from .util import define_examples_context


def test_presets_on_examples(snapshot):
    context = define_examples_context()
    for pipeline_name in sorted(context.get_repository_definition().pipeline_names):
        snapshot.assert_match(execute_preset_query(pipeline_name, context).data)
