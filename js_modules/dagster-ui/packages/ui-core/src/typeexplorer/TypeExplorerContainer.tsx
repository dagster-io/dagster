import {TYPE_EXPLORER_FRAGMENT, TypeExplorer} from './TypeExplorer';
import {
  TypeExplorerContainerQuery,
  TypeExplorerContainerQueryVariables,
} from './types/TypeExplorerContainer.types';
import {gql, useQuery} from '../apollo-client';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {Loading} from '../ui/Loading';
import {buildPipelineSelector} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

interface ITypeExplorerContainerProps {
  explorerPath: ExplorerPath;
  typeName: string;
  repoAddress?: RepoAddress;
}

export const TypeExplorerContainer = ({
  explorerPath,
  typeName,
  repoAddress,
}: ITypeExplorerContainerProps) => {
  const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);
  const queryResult = useQuery<TypeExplorerContainerQuery, TypeExplorerContainerQueryVariables>(
    TYPE_EXPLORER_CONTAINER_QUERY,
    {
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
      ... on Pipeline {
        id
        isJob
        dagsterTypeOrError(dagsterTypeName: $dagsterTypeName) {
          ... on RegularDagsterType {
            ...TypeExplorerFragment
          }
        }
      }
    }
  }

  ${TYPE_EXPLORER_FRAGMENT}
`;
