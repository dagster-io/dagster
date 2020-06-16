from dagster_examples.toys.repo import toys_repository
from dagster_examples.toys.tree_demo import generate_solid

from dagster import execute_pipeline


def test_guide_pipelines_success():
    tree_repo = toys_repository
    pipeline_result = execute_pipeline(
        tree_repo.get_pipeline('demo_tree_pipeline'),
        run_config={'solids': {'0_solid': {'inputs': {'parent': {'value': 1}}}}},
    )
    assert pipeline_result.success


def test_generate_solid():
    generated_solid_def = generate_solid('foo', 3)
    assert generated_solid_def.name == 'foo'
    assert generated_solid_def.input_defs[0].name == 'parent'
