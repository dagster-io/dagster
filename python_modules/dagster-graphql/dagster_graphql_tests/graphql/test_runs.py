import copy

from dagster_graphql.test.utils import define_context_for_file, execute_dagster_graphql

from dagster import RepositoryDefinition, execute_pipeline, lambda_solid, pipeline
from dagster.core.instance import DagsterInstance

RUNS_QUERY = '''
query PipelineRunsRootQuery($name: String!) {
  pipeline(params: { name: $name }) {
    ...on PipelineReference { name }
    ... on Pipeline {
      runs {
        ...RunHistoryRunFragment
      }
    }
  }
}

fragment RunHistoryRunFragment on PipelineRun {
  runId
  status
  pipeline {
    ...on PipelineReference { name }
  }
  logs {
    nodes {
      __typename
      ... on MessageEvent {
        timestamp
      }
    }
  }
  executionPlan {
    steps {
      key
    }
  }
  environmentConfigYaml
  mode
  canCancel
}
'''

DELETE_RUN_MUTATION = '''
mutation DeleteRun($runId: String!) {
  deletePipelineRun(runId: $runId) {
    __typename
    ... on DeletePipelineRunSuccess {
      runId
    }
    ... on PythonError {
      message
    }
  }
}
'''


ALL_RUNS_QUERY = '''
{
  pipelineRunsOrError{
    ... on PipelineRuns {
      results {
        runId
        pipeline {
          __typename
          ... on PipelineReference {
            name
          }
        }
        executionSelection {
          name
          solidSubset
        }
      }
    }
  }
}
'''


def _get_runs_data(result, run_id):
    for run_data in result.data['pipeline']['runs']:
        if run_data['runId'] == run_id:
            # so caller can delete keys
            return copy.deepcopy(run_data)

    return None


def test_get_runs_over_graphql():
    from .utils import (
        define_test_context,
        sync_execute_get_run_log_data,
    )

    payload_one = sync_execute_get_run_log_data(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'add_mode',
                'environmentConfigData': {'resources': {'op': {'config': 2}}},
            }
        }
    )
    run_id_one = payload_one['run']['runId']

    payload_two = sync_execute_get_run_log_data(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'add_mode',
                'environmentConfigData': {'resources': {'op': {'config': 3}}},
            }
        }
    )

    run_id_two = payload_two['run']['runId']

    read_context = define_test_context(instance=DagsterInstance.local_temp())

    result = execute_dagster_graphql(
        read_context, RUNS_QUERY, variables={'name': 'multi_mode_with_resources'}
    )

    run_one_data = _get_runs_data(result, run_id_one)
    assert [log['__typename'] for log in run_one_data['logs']['nodes']] == [
        msg['__typename'] for msg in payload_one['messages']
    ]

    run_two_data = _get_runs_data(result, run_id_two)
    assert [log['__typename'] for log in run_two_data['logs']['nodes']] == [
        msg['__typename'] for msg in payload_two['messages']
    ]

    # delete the second run
    result = execute_dagster_graphql(
        read_context, DELETE_RUN_MUTATION, variables={'runId': run_id_two}
    )
    assert result.data['deletePipelineRun']['__typename'] == 'DeletePipelineRunSuccess'
    assert result.data['deletePipelineRun']['runId'] == run_id_two

    # query it back out
    result = execute_dagster_graphql(
        read_context, RUNS_QUERY, variables={'name': 'multi_mode_with_resources'}
    )

    # first is the same
    run_one_data = _get_runs_data(result, run_id_one)
    assert [log['__typename'] for log in run_one_data['logs']['nodes']] == [
        msg['__typename'] for msg in payload_one['messages']
    ]

    # second is gone
    run_two_data = _get_runs_data(result, run_id_two)
    assert run_two_data is None

    # try to delete the second run again
    execute_dagster_graphql(read_context, DELETE_RUN_MUTATION, variables={'runId': run_id_two})

    result = execute_dagster_graphql(
        read_context, DELETE_RUN_MUTATION, variables={'runId': run_id_two}
    )
    assert result.data['deletePipelineRun']['__typename'] == 'PipelineRunNotFoundError'


def get_repo_at_time_1():
    @lambda_solid
    def solid_A():
        pass

    @lambda_solid
    def solid_B():
        pass

    @pipeline
    def evolving_pipeline():
        solid_A()
        solid_B()

    @pipeline
    def foo_pipeline():
        solid_A()

    return RepositoryDefinition('evolving_repo', pipeline_defs=[evolving_pipeline, foo_pipeline])


def get_repo_at_time_2():
    @lambda_solid
    def solid_A():
        pass

    @lambda_solid
    def solid_B_prime():
        pass

    @pipeline
    def evolving_pipeline():
        solid_A()
        solid_B_prime()

    @pipeline
    def bar_pipeline():
        solid_A()

    return RepositoryDefinition('evolving_repo', pipeline_defs=[evolving_pipeline, bar_pipeline])


def test_runs_over_time():
    instance = DagsterInstance.local_temp()

    repo_1 = get_repo_at_time_1()

    full_evolve_run_id = execute_pipeline(
        repo_1.get_pipeline('evolving_pipeline'), instance=instance
    ).run_id
    foo_run_id = execute_pipeline(repo_1.get_pipeline('foo_pipeline'), instance=instance).run_id
    evolve_a_run_id = execute_pipeline(
        repo_1.get_pipeline('evolving_pipeline').build_sub_pipeline(['solid_A']), instance=instance
    ).run_id
    evolve_b_run_id = execute_pipeline(
        repo_1.get_pipeline('evolving_pipeline').build_sub_pipeline(['solid_B']), instance=instance
    ).run_id

    context_at_time_1 = define_context_for_file(__file__, 'get_repo_at_time_1', instance)

    result = execute_dagster_graphql(context_at_time_1, ALL_RUNS_QUERY)
    assert result.data

    t1_runs = {run['runId']: run for run in result.data['pipelineRunsOrError']['results']}

    assert t1_runs[full_evolve_run_id]['pipeline']['__typename'] == 'Pipeline'
    assert t1_runs[full_evolve_run_id]['executionSelection'] == {
        'name': 'evolving_pipeline',
        'solidSubset': None,
    }
    assert t1_runs[foo_run_id]['pipeline']['__typename'] == 'Pipeline'
    assert t1_runs[foo_run_id]['executionSelection'] == {
        'name': 'foo_pipeline',
        'solidSubset': None,
    }
    assert t1_runs[evolve_a_run_id]['pipeline']['__typename'] == 'Pipeline'
    assert t1_runs[evolve_a_run_id]['executionSelection'] == {
        'name': 'evolving_pipeline',
        'solidSubset': ['solid_A'],
    }
    assert t1_runs[evolve_b_run_id]['pipeline']['__typename'] == 'Pipeline'
    assert t1_runs[evolve_b_run_id]['executionSelection'] == {
        'name': 'evolving_pipeline',
        'solidSubset': ['solid_B'],
    }

    context_at_time_2 = define_context_for_file(__file__, 'get_repo_at_time_2', instance)

    result = execute_dagster_graphql(context_at_time_2, ALL_RUNS_QUERY)
    assert result.data

    t2_runs = {run['runId']: run for run in result.data['pipelineRunsOrError']['results']}

    assert t2_runs[full_evolve_run_id]['pipeline']['__typename'] == 'Pipeline'
    assert t1_runs[full_evolve_run_id]['executionSelection'] == {
        'name': 'evolving_pipeline',
        'solidSubset': None,
    }
    assert t2_runs[evolve_a_run_id]['pipeline']['__typename'] == 'Pipeline'
    assert t2_runs[evolve_a_run_id]['executionSelection'] == {
        'name': 'evolving_pipeline',
        'solidSubset': ['solid_A'],
    }
    # pipeline name changed
    assert t2_runs[foo_run_id]['pipeline']['__typename'] == 'UnknownPipeline'
    assert t1_runs[foo_run_id]['executionSelection'] == {
        'name': 'foo_pipeline',
        'solidSubset': None,
    }
    # subset no longer valid - b renamed
    assert t2_runs[evolve_b_run_id]['pipeline']['__typename'] == 'UnknownPipeline'
    assert t2_runs[evolve_b_run_id]['executionSelection'] == {
        'name': 'evolving_pipeline',
        'solidSubset': ['solid_B'],
    }
