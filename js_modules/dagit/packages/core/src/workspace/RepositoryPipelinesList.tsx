import {gql, useQuery} from '@apollo/client';
import {Box, NonIdealState} from '@dagster-io/ui';
import * as React from 'react';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PipelineTable, PIPELINE_TABLE_FRAGMENT} from '../pipelines/PipelineTable';

import {repoAddressAsString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {
  RepositoryPipelinesListQuery,
  RepositoryPipelinesListQueryVariables,
} from './types/RepositoryPipelinesListQuery';

const REPOSITORY_PIPELINES_LIST_QUERY = gql`
  query RepositoryPipelinesListQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        pipelines {
          id
          ...PipelineTableFragment
        }
      }
      ... on RepositoryNotFoundError {
        message
      }
    }
  }
  ${PIPELINE_TABLE_FRAGMENT}
`;

interface Props {
  repoAddress: RepoAddress;
  display: 'jobs' | 'pipelines';
}

export const RepositoryPipelinesList: React.FC<Props> = (props) => {
  const {display, repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<
    RepositoryPipelinesListQuery,
    RepositoryPipelinesListQueryVariables
  >(REPOSITORY_PIPELINES_LIST_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {repositorySelector},
  });

  const repo = data?.repositoryOrError;
  const pipelinesForTable = React.useMemo(() => {
    if (!repo || repo.__typename !== 'Repository') {
      return null;
    }
    return repo.pipelines
      .filter((pipelineOrJob) => !isHiddenAssetGroupJob(pipelineOrJob.name))
      .map((pipelineOrJob) => ({
        pipelineOrJob,
        repoAddress,
      }))
      .filter(({pipelineOrJob}) =>
        display === 'jobs' ? pipelineOrJob.isJob : !pipelineOrJob.isJob,
      );
  }, [display, repo, repoAddress]);

  if (loading) {
    return null;
  }

  if (error || !pipelinesForTable) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Unable to load pipelines"
          description={`Could not load pipelines for ${repoAddressAsString(repoAddress)}`}
        />
      </Box>
    );
  }

  if (!pipelinesForTable.length) {
    return (
      <Box padding={64}>
        <NonIdealState
          icon="job"
          title={display === 'jobs' ? 'No jobs found' : 'No pipelines found'}
          description={
            <div>
              {display === 'jobs'
                ? 'This repository does not have any jobs defined.'
                : 'This repository does not have any pipelines defined.'}
            </div>
          }
        />
      </Box>
    );
  }

  return <PipelineTable pipelinesOrJobs={pipelinesForTable} showRepo={false} />;
};
