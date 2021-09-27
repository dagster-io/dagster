import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PipelineTable, PIPELINE_TABLE_FRAGMENT} from '../pipelines/PipelineTable';
import {NonIdealState} from '../ui/NonIdealState';

import {repoAddressAsString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {RepositoryPipelinesListQuery} from './types/RepositoryPipelinesListQuery';

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
}

export const RepositoryPipelinesList: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<RepositoryPipelinesListQuery>(
    REPOSITORY_PIPELINES_LIST_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {repositorySelector},
    },
  );

  const repo = data?.repositoryOrError;
  const pipelinesForTable = React.useMemo(() => {
    if (!repo || repo.__typename !== 'Repository') {
      return null;
    }
    return repo.pipelines.map((pipeline) => ({
      pipeline,
      repoAddress,
    }));
  }, [repo, repoAddress]);

  if (loading) {
    return null;
  }

  if (error || !pipelinesForTable) {
    return (
      <NonIdealState
        icon="error"
        title="Unable to load pipelines"
        description={`Could not load pipelines for ${repoAddressAsString(repoAddress)}`}
      />
    );
  }

  return <PipelineTable pipelines={pipelinesForTable} showRepo={false} />;
};
