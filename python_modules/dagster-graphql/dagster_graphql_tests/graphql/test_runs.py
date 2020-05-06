import copy

from dagster_graphql.test.utils import define_context_for_file, execute_dagster_graphql

from dagster import RepositoryDefinition, RunConfig, execute_pipeline, lambda_solid, pipeline, seven
from dagster.core.instance import DagsterInstance
from dagster.core.storage.tags import PARENT_RUN_ID_TAG, ROOT_RUN_ID_TAG

RUNS_QUERY = '''
query PipelineRunsRootQuery($name: String!) {
  pipeline(params: { name: $name }) {
    ... on PipelineReference { name }
    ... on Pipeline {
      pipelineSnapshotId
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
        pipelineSnapshotId
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

FILTERED_RUN_QUERY = '''
query PipelineRunsRootQuery($filter: PipelineRunsFilter!) {
  pipelineRunsOrError(filter: $filter) {
    ... on PipelineRuns {
      results {
        runId
      }
    }
  }
}
'''


RUN_GROUP_QUERY = '''
query RunGroupQuery($runId: ID!) {
  runGroupOrError(runId: $runId) {
    ... on RunGroup {
      __typename
      rootRunId
      runs {
        runId
        pipeline {
          __typename
          ... on PipelineReference {
            name
          }
        }
      }
    }
    ... on RunGroupNotFoundError {
      __typename
      runId
      message
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
    assert run_one_data

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
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        repo_1 = get_repo_at_time_1()

        full_evolve_run_id = execute_pipeline(
            repo_1.get_pipeline('evolving_pipeline'), instance=instance
        ).run_id
        foo_run_id = execute_pipeline(repo_1.get_pipeline('foo_pipeline'), instance=instance).run_id
        evolve_a_run_id = execute_pipeline(
            repo_1.get_pipeline('evolving_pipeline').build_sub_pipeline(['solid_A']),
            instance=instance,
        ).run_id
        evolve_b_run_id = execute_pipeline(
            repo_1.get_pipeline('evolving_pipeline').build_sub_pipeline(['solid_B']),
            instance=instance,
        ).run_id

        context_at_time_1 = define_context_for_file(__file__, 'get_repo_at_time_1', instance)

        result = execute_dagster_graphql(context_at_time_1, ALL_RUNS_QUERY)
        assert result.data

        t1_runs = {run['runId']: run for run in result.data['pipelineRunsOrError']['results']}

        # test full_evolve_run_id
        assert t1_runs[full_evolve_run_id]['pipeline']['__typename'] == 'Pipeline'
        assert t1_runs[full_evolve_run_id]['executionSelection'] == {
            'name': 'evolving_pipeline',
            'solidSubset': None,
        }

        # test foo_run_id
        assert t1_runs[foo_run_id]['pipeline']['__typename'] == 'Pipeline'
        assert t1_runs[foo_run_id]['executionSelection'] == {
            'name': 'foo_pipeline',
            'solidSubset': None,
        }

        # test evolve_a_run_id
        assert t1_runs[evolve_a_run_id]['pipeline']['__typename'] == 'Pipeline'
        assert t1_runs[evolve_a_run_id]['executionSelection'] == {
            'name': 'evolving_pipeline',
            'solidSubset': ['solid_A'],
        }
        assert t1_runs[evolve_a_run_id]['pipelineSnapshotId']

        # test evolve_b_run_id
        assert t1_runs[evolve_b_run_id]['pipeline']['__typename'] == 'Pipeline'
        assert t1_runs[evolve_b_run_id]['executionSelection'] == {
            'name': 'evolving_pipeline',
            'solidSubset': ['solid_B'],
        }

        context_at_time_2 = define_context_for_file(__file__, 'get_repo_at_time_2', instance)

        result = execute_dagster_graphql(context_at_time_2, ALL_RUNS_QUERY)
        assert result.data

        t2_runs = {run['runId']: run for run in result.data['pipelineRunsOrError']['results']}

        # test full_evolve_run_id
        assert t2_runs[full_evolve_run_id]['pipeline']['__typename'] == 'Pipeline'
        assert t1_runs[full_evolve_run_id]['executionSelection'] == {
            'name': 'evolving_pipeline',
            'solidSubset': None,
        }

        # test evolve_a_run_id
        assert t2_runs[evolve_a_run_id]['pipeline']['__typename'] == 'Pipeline'
        assert t2_runs[evolve_a_run_id]['executionSelection'] == {
            'name': 'evolving_pipeline',
            'solidSubset': ['solid_A'],
        }
        assert t2_runs[evolve_a_run_id]['pipelineSnapshotId']

        # names same
        assert (
            t1_runs[full_evolve_run_id]['pipeline']['name']
            == t2_runs[evolve_a_run_id]['pipeline']['name']
        )

        # snapshots differ
        assert (
            t1_runs[full_evolve_run_id]['pipelineSnapshotId']
            != t2_runs[evolve_a_run_id]['pipelineSnapshotId']
        )

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


def test_filtered_runs():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        repo = get_repo_at_time_1()
        run_id_1 = execute_pipeline(
            repo.get_pipeline('foo_pipeline'), instance=instance, tags={'run': 'one'}
        ).run_id
        _run_id_2 = execute_pipeline(
            repo.get_pipeline('foo_pipeline'), instance=instance, tags={'run': 'two'}
        ).run_id
        context = define_context_for_file(__file__, 'get_repo_at_time_1', instance)
        result = execute_dagster_graphql(
            context, FILTERED_RUN_QUERY, variables={'filter': {'runId': run_id_1}}
        )
        assert result.data
        run_ids = [run['runId'] for run in result.data['pipelineRunsOrError']['results']]
        assert len(run_ids) == 1
        assert run_ids[0] == run_id_1

        result = execute_dagster_graphql(
            context,
            FILTERED_RUN_QUERY,
            variables={'filter': {'tags': [{'key': 'run', 'value': 'one'}]}},
        )
        assert result.data
        run_ids = [run['runId'] for run in result.data['pipelineRunsOrError']['results']]
        assert len(run_ids) == 1
        assert run_ids[0] == run_id_1


def test_run_group():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        repo = get_repo_at_time_1()
        foo_pipeline = repo.get_pipeline('foo_pipeline')
        runs = [execute_pipeline(foo_pipeline, instance=instance)]
        root_run_id = runs[-1].run_id
        for _ in range(3):
            # https://github.com/dagster-io/dagster/issues/2433
            runs.append(
                execute_pipeline(
                    foo_pipeline,
                    run_config=RunConfig(previous_run_id=root_run_id),
                    tags={PARENT_RUN_ID_TAG: root_run_id, ROOT_RUN_ID_TAG: root_run_id},
                    instance=instance,
                )
            )

        context_at_time_1 = define_context_for_file(__file__, 'get_repo_at_time_1', instance)

        result_one = execute_dagster_graphql(
            context_at_time_1, RUN_GROUP_QUERY, variables={'runId': root_run_id},
        )
        assert result_one.data['runGroupOrError']['__typename'] == 'RunGroup'

        assert len(result_one.data['runGroupOrError']['runs']) == 4

        result_two = execute_dagster_graphql(
            context_at_time_1, RUN_GROUP_QUERY, variables={'runId': runs[-1].run_id},
        )
        assert result_one.data['runGroupOrError']['__typename'] == 'RunGroup'
        assert len(result_two.data['runGroupOrError']['runs']) == 4

        assert (
            result_one.data['runGroupOrError']['rootRunId']
            == result_two.data['runGroupOrError']['rootRunId']
        )
        assert (
            result_one.data['runGroupOrError']['runs'] == result_two.data['runGroupOrError']['runs']
        )


def test_run_group_not_found():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        context_at_time_1 = define_context_for_file(__file__, 'get_repo_at_time_1', instance)

        result = execute_dagster_graphql(
            context_at_time_1, RUN_GROUP_QUERY, variables={'runId': 'foo'},
        )
        assert result.data
        assert result.data['runGroupOrError']
        assert result.data['runGroupOrError']['__typename'] == 'RunGroupNotFoundError'
        assert result.data['runGroupOrError']['runId'] == 'foo'
        assert result.data['runGroupOrError'][
            'message'
        ] == 'Run group of run {run_id} could not be found.'.format(run_id='foo')
