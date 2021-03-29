import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PipelineExplorerPath} from '../pipelines/PipelinePathUtils';
import {Loading} from '../ui/Loading';
import {usePipelineSelector} from '../workspace/WorkspaceContext';

import {TypeList, TYPE_LIST_FRAGMENT} from './TypeList';
import {TypeListContainerQuery} from './types/TypeListContainerQuery';

interface ITypeListContainerProps {
  explorerPath: PipelineExplorerPath;
}

export const TypeListContainer: React.FunctionComponent<ITypeListContainerProps> = ({
  explorerPath,
}) => {
  const pipelineSelector = usePipelineSelector(explorerPath.pipelineName);
  const queryResult = useQuery<TypeListContainerQuery>(TYPE_LIST_CONTAINER_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {pipelineSelector},
  });

  return (
    <Loading queryResult={queryResult}>
      {(data) => {
        if (data.pipelineOrError.__typename === 'Pipeline') {
          return <TypeList types={data.pipelineOrError.dagsterTypes} />;
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
        name
        dagsterTypes {
          ...TypeListFragment
        }
      }
    }
  }

  ${TYPE_LIST_FRAGMENT}
`;
