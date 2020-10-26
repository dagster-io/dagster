import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {usePipelineSelector} from 'src/DagsterRepositoryContext';
import {Loading} from 'src/Loading';
import {PipelineExplorerPath} from 'src/PipelinePathUtils';
import {TypeList} from 'src/typeexplorer/TypeList';
import {TypeListContainerQuery} from 'src/typeexplorer/types/TypeListContainerQuery';

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

export const TYPE_LIST_CONTAINER_QUERY = gql`
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

  ${TypeList.fragments.TypeListFragment}
`;
