from dagster_examples.pyspark_pagerank.repository import define_repository

from dagster import execute_pipeline
from dagster.utils import script_relative_path

from .util import checks_for_helper_functions


def test_pyspark_pagerank_repo():
    assert define_repository().get_all_pipelines()


def test_run_step_one():
    assert execute_pipeline(define_repository().get_pipeline('pyspark_pagerank_step_one')).success


def test_run_step_two():
    result = execute_pipeline(
        define_repository().get_pipeline('pyspark_pagerank_step_two'),
        environment_dict={
            'solids': {
                'whole_pipeline_solid': {
                    'inputs': {'pagerank_data': script_relative_path('pagerank_data.txt')}
                }
            }
        },
    )
    assert result.success

    assert set(result.result_for_solid('whole_pipeline_solid').output_value()) == {
        ('anotherlessimportantsite.com', 0.9149999999999999),
        ('whatdoesitallmeananyways.com', 0.9149999999999999),
        ('importantsite.com', 1.255),
        ('alessimportantsite.com', 0.9149999999999999),
    }


def test_step_two_fns():
    from dagster_examples.pyspark_pagerank.steps.step_two import computeContribs, parseNeighbors

    checks_for_helper_functions(computeContribs, parseNeighbors)


def test_run_step_three():
    result = execute_pipeline(
        define_repository().get_pipeline('pyspark_pagerank_step_three'),
        environment_dict={
            'solids': {
                'whole_pipeline_solid_using_context': {
                    'inputs': {'pagerank_data': script_relative_path('pagerank_data.txt')}
                }
            }
        },
    )
    assert result.success

    assert set(result.result_for_solid('whole_pipeline_solid_using_context').output_value()) == {
        ('anotherlessimportantsite.com', 0.9149999999999999),
        ('whatdoesitallmeananyways.com', 0.9149999999999999),
        ('importantsite.com', 1.255),
        ('alessimportantsite.com', 0.9149999999999999),
    }


def test_step_three_fns():
    from dagster_examples.pyspark_pagerank.steps.step_three import computeContribs, parseNeighbors

    checks_for_helper_functions(computeContribs, parseNeighbors)


def test_run_step_four():
    result = execute_pipeline(
        define_repository().get_pipeline('pyspark_pagerank_step_four'),
        environment_dict={
            'solids': {
                'parse_pagerank_data_step_four': {
                    'inputs': {'pagerank_data': script_relative_path('pagerank_data.txt')}
                }
            }
        },
    )
    assert result.success

    assert set(result.result_for_solid('rest_of_pipeline').output_value()) == {
        ('anotherlessimportantsite.com', 0.9149999999999999),
        ('whatdoesitallmeananyways.com', 0.9149999999999999),
        ('importantsite.com', 1.255),
        ('alessimportantsite.com', 0.9149999999999999),
    }


def test_step_four_fns():
    from dagster_examples.pyspark_pagerank.steps.step_four import computeContribs, parseNeighbors

    checks_for_helper_functions(computeContribs, parseNeighbors)


def test_run_step_five():
    result = execute_pipeline(
        define_repository().get_pipeline('pyspark_pagerank_step_five'),
        environment_dict={
            'solids': {
                'parse_pagerank_data_step_five': {
                    'inputs': {'pagerank_data': script_relative_path('pagerank_data.txt')}
                },
                'calculate_ranks_step_five': {'config': {'iterations': 3}},
            }
        },
    )
    assert result.success

    assert set(result.result_for_solid('log_ranks_step_five').output_value()) == {
        ('alessimportantsite.com', 0.5055833333333333),
        ('whatdoesitallmeananyways.com', 0.5055833333333333),
        ('importantsite.com', 2.4832499999999995),
        ('anotherlessimportantsite.com', 0.5055833333333333),
    }


def test_step_five_fns():
    from dagster_examples.pyspark_pagerank.steps.step_five import computeContribs, parseNeighbors

    checks_for_helper_functions(computeContribs, parseNeighbors)


def test_run_final_example():
    result = execute_pipeline(
        define_repository().get_pipeline('pyspark_pagerank'),
        environment_dict={
            'solids': {
                'parse_pagerank_data': {
                    'inputs': {'pagerank_data': script_relative_path('pagerank_data.txt')}
                },
                'calculate_ranks': {'config': {'iterations': 3}},
            }
        },
    )
    assert result.success

    assert set(result.result_for_solid('log_ranks').output_value()) == {
        ('alessimportantsite.com', 0.5055833333333333),
        ('whatdoesitallmeananyways.com', 0.5055833333333333),
        ('importantsite.com', 2.4832499999999995),
        ('anotherlessimportantsite.com', 0.5055833333333333),
    }
