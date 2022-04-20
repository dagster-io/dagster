import {gql, useQuery} from '@apollo/client';
import {Box, NonIdealState} from '@dagster-io/ui';
import * as React from 'react';

import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {Loading} from '../ui/Loading';
import {
  buildPipelineSelector,
  optionToRepoAddress,
  useRepositoryOptions,
} from '../workspace/WorkspaceContext';
import {findRepoContainingPipeline} from '../workspace/findRepoContainingPipeline';
import {RepoAddress} from '../workspace/types';

import {TypeList, TYPE_LIST_FRAGMENT} from './TypeList';
import {
  TypeListContainerQuery,
  TypeListContainerQueryVariables,
} from './types/TypeListContainerQuery';

interface ITypeListContainerProps {
  explorerPath: ExplorerPath;
  repoAddress?: RepoAddress;
}

export const TypeListContainer: React.FC<ITypeListContainerProps> = ({
  explorerPath,
  repoAddress,
}) => {
  const {pipelineName, snapshotId} = explorerPath;
  const {options} = useRepositoryOptions();

  const pipelineSelector = React.useMemo(() => {
    if (!repoAddress) {
      const reposWithMatch = findRepoContainingPipeline(options, pipelineName, snapshotId);
      return reposWithMatch.length
        ? buildPipelineSelector(optionToRepoAddress(reposWithMatch[0]), pipelineName)
        : null;
    }
    return buildPipelineSelector(repoAddress, pipelineName);
  }, [options, pipelineName, repoAddress, snapshotId]);

  const queryResult = useQuery<TypeListContainerQuery, TypeListContainerQueryVariables>(
    TYPE_LIST_CONTAINER_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {pipelineSelector: pipelineSelector!},
      skip: !pipelineSelector,
    },
  );

  if (!pipelineSelector) {
    return (
      <Box margin={48}>
        <NonIdealState icon="error" title="Could not fetch types for snapshot" />
      </Box>
    );
  }

  return (
    <Loading queryResult={queryResult}>
      {(data) => {
        if (data.pipelineOrError.__typename === 'Pipeline') {
          return (
            <TypeList
              types={data.pipelineOrError.dagsterTypes}
              isGraph={data.pipelineOrError.isJob}
            />
          );
        } else {
          return null;
        }
      }}
    </Loading>
  );
};

const TYPE_LIST_CONTAINER_QUERY = gql`
  query TypeListContainerQuery($pipelineSelector: PipelineSelector!) {
    pipelineOrError(params: $pipelineSelector) {
      __typename
      ... on Pipeline {
        id
        isJob
        name
        dagsterTypes {
          ...TypeListFragment
        }
      }
    }
  }

  ${TYPE_LIST_FRAGMENT}
`;
