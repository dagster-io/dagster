import {Box, NonIdealState} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {TYPE_LIST_FRAGMENT, TypeList} from './TypeList';
import {
  TypeListContainerQuery,
  TypeListContainerQueryVariables,
} from './types/TypeListContainer.types';
import {gql, useQuery} from '../apollo-client';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {Loading} from '../ui/Loading';
import {
  buildPipelineSelector,
  optionToRepoAddress,
  useRepositoryOptions,
} from '../workspace/WorkspaceContext/util';
import {findRepoContainingPipeline} from '../workspace/findRepoContainingPipeline';
import {RepoAddress} from '../workspace/types';

interface ITypeListContainerProps {
  explorerPath: ExplorerPath;
  repoAddress?: RepoAddress;
}

export const TypeListContainer = ({explorerPath, repoAddress}: ITypeListContainerProps) => {
  const {pipelineName, snapshotId} = explorerPath;
  const {options} = useRepositoryOptions();

  const pipelineSelector = useMemo(() => {
    if (!repoAddress) {
      const reposWithMatch = findRepoContainingPipeline(options, pipelineName, snapshotId);
      return reposWithMatch[0]
        ? buildPipelineSelector(optionToRepoAddress(reposWithMatch[0]), pipelineName)
        : null;
    }
    return buildPipelineSelector(repoAddress, pipelineName);
  }, [options, pipelineName, repoAddress, snapshotId]);

  const queryResult = useQuery<TypeListContainerQuery, TypeListContainerQueryVariables>(
    TYPE_LIST_CONTAINER_QUERY,
    {
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
