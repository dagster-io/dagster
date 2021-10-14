import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PipelineExplorerPath} from '../pipelines/PipelinePathUtils';
import {Loading} from '../ui/Loading';
import {usePipelineSelector} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {TypeList, TYPE_LIST_FRAGMENT} from './TypeList';
import {TypeListContainerQuery} from './types/TypeListContainerQuery';

interface ITypeListContainerProps {
  explorerPath: PipelineExplorerPath;
  repoAddress?: RepoAddress;
}

export const TypeListContainer: React.FunctionComponent<ITypeListContainerProps> = ({
  explorerPath,
  repoAddress,
}) => {
  const pipelineSelector = usePipelineSelector(repoAddress || null, explorerPath.pipelineName);
  const queryResult = useQuery<TypeListContainerQuery>(TYPE_LIST_CONTAINER_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {pipelineSelector},
  });

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
