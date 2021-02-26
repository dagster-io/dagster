import {gql, useQuery} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';

import {PipelineTable, PIPELINE_TABLE_FRAGMENT} from 'src/pipelines/PipelineTable';
import {Page} from 'src/ui/Page';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {RepositoryPipelinesListQuery} from 'src/workspace/types/RepositoryPipelinesListQuery';

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
        title="Unable to load pipelines"
        description={`Could not load pipelines for ${repoAddressAsString(repoAddress)}`}
      />
    );
  }

  return (
    <Page>
      <PipelineTable pipelines={pipelinesForTable} showRepo={false} />
    </Page>
  );
};
