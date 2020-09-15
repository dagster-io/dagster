import gql from 'graphql-tag';
import * as React from 'react';
import Loading from '../Loading';
import {useQuery} from 'react-apollo';
import TypeList from './TypeList';
import {TypeListContainerQuery} from './types/TypeListContainerQuery';
import {PipelineExplorerPath} from '../PipelinePathUtils';
import {usePipelineSelector} from '../DagsterRepositoryContext';

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
