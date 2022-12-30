import {useQuery} from '@apollo/client';
import * as React from 'react';

import {graphql} from '../graphql';
import {PipelineSelector} from '../graphql/graphql';
import {NonIdealPipelineQueryResult} from '../pipelines/NonIdealPipelineQueryResult';
import {SidebarContainerOverview} from '../pipelines/SidebarContainerOverview';
import {Loading} from '../ui/Loading';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

export const AssetGraphJobSidebar: React.FC<{
  pipelineSelector: PipelineSelector;
}> = ({pipelineSelector}) => {
  const queryResult = useQuery(ASSET_GRAPH_JOB_SIDEBAR, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    variables: {pipelineSelector},
  });

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

const ASSET_GRAPH_JOB_SIDEBAR = graphql(`
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
`);
