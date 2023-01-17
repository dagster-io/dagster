import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PipelineSelector} from '../graphql/types';
import {NonIdealPipelineQueryResult} from '../pipelines/NonIdealPipelineQueryResult';
import {
  SidebarContainerOverview,
  SIDEBAR_ROOT_CONTAINER_FRAGMENT,
} from '../pipelines/SidebarContainerOverview';
import {Loading} from '../ui/Loading';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {
  AssetGraphSidebarQuery,
  AssetGraphSidebarQueryVariables,
} from './types/AssetGraphJobSidebar.types';

export const AssetGraphJobSidebar: React.FC<{
  pipelineSelector: PipelineSelector;
}> = ({pipelineSelector}) => {
  const queryResult = useQuery<AssetGraphSidebarQuery, AssetGraphSidebarQueryVariables>(
    ASSET_GRAPH_JOB_SIDEBAR,
    {
      partialRefetch: true,
      variables: {pipelineSelector},
    },
  );

  const {repositoryName, repositoryLocationName} = pipelineSelector;
  const repoAddress = buildRepoAddress(repositoryName, repositoryLocationName);

  return (
    <Loading queryResult={queryResult}>
      {({pipelineSnapshotOrError}) => {
        if (pipelineSnapshotOrError.__typename !== 'PipelineSnapshot') {
          return (
            <NonIdealPipelineQueryResult
              isGraph
              result={pipelineSnapshotOrError}
              repoAddress={repoAddress}
            />
          );
        }
        return (
          <SidebarContainerOverview container={pipelineSnapshotOrError} repoAddress={repoAddress} />
        );
      }}
    </Loading>
  );
};

const ASSET_GRAPH_JOB_SIDEBAR = gql`
  query AssetGraphSidebarQuery($pipelineSelector: PipelineSelector!) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        id
        ...SidebarRootContainerFragment
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineSnapshotNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${SIDEBAR_ROOT_CONTAINER_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
