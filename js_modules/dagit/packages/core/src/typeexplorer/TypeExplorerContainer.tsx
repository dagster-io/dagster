import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PipelineExplorerPath} from '../pipelines/PipelinePathUtils';
import {Loading} from '../ui/Loading';
import {buildPipelineSelector} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {TypeExplorer, TYPE_EXPLORER_FRAGMENT} from './TypeExplorer';
import {
  TypeExplorerContainerQuery,
  TypeExplorerContainerQueryVariables,
} from './types/TypeExplorerContainerQuery';

interface ITypeExplorerContainerProps {
  explorerPath: PipelineExplorerPath;
  typeName: string;
  repoAddress?: RepoAddress;
}

export const TypeExplorerContainer: React.FC<ITypeExplorerContainerProps> = ({
  explorerPath,
  typeName,
  repoAddress,
}) => {
  const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);
  const queryResult = useQuery<TypeExplorerContainerQuery, TypeExplorerContainerQueryVariables>(
    TYPE_EXPLORER_CONTAINER_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {
        pipelineSelector,
        dagsterTypeName: typeName,
      },
    },
  );
  return (
    <Loading queryResult={queryResult}>
      {(data) => {
        if (
          data.pipelineOrError &&
          data.pipelineOrError.__typename === 'Pipeline' &&
          data.pipelineOrError.dagsterTypeOrError &&
          data.pipelineOrError.dagsterTypeOrError.__typename === 'RegularDagsterType'
        ) {
          return (
            <TypeExplorer
              isGraph={data.pipelineOrError.isJob}
              type={data.pipelineOrError.dagsterTypeOrError}
            />
          );
        } else {
          return <div>Type Not Found</div>;
        }
      }}
    </Loading>
  );
};

const TYPE_EXPLORER_CONTAINER_QUERY = gql`
  query TypeExplorerContainerQuery(
    $pipelineSelector: PipelineSelector!
    $dagsterTypeName: String!
  ) {
    pipelineOrError(params: $pipelineSelector) {
      __typename
      ... on Pipeline {
        id
        isJob
        dagsterTypeOrError(dagsterTypeName: $dagsterTypeName) {
          __typename
          ... on RegularDagsterType {
            ...TypeExplorerFragment
          }
        }
      }
    }
  }
  ${TYPE_EXPLORER_FRAGMENT}
`;
