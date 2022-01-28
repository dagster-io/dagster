import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Loading} from '../ui/Loading';
import {buildPipelineSelector} from '../workspace/WorkspaceContext';
import {AssetGraphExplorer} from '../workspace/asset-graph/AssetGraphExplorer';
import {RepoAddress} from '../workspace/types';

import {explodeCompositesInHandleGraph} from './CompositeSupport';
import {
  GraphExplorer,
  GraphExplorerOptions,
  GRAPH_EXPLORER_FRAGMENT,
  GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT,
} from './GraphExplorer';
import {NonIdealPipelineQueryResult} from './NonIdealPipelineQueryResult';
import {ExplorerPath, explorerPathFromString, explorerPathToString} from './PipelinePathUtils';
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQueryVariables,
} from './types/PipelineExplorerRootQuery';

export const PipelineExplorerSnapshotRoot = () => {
  const params = useParams();
  const explorerPath = explorerPathFromString(params['0']);
  const {pipelineName, snapshotId} = explorerPath;
  const history = useHistory();

  useDocumentTitle(`Snapshot: ${pipelineName}${snapshotId ? `@${snapshotId.slice(0, 8)}` : ''}`);

  return (
    <PipelineExplorerContainer
      explorerPath={explorerPath}
      onChangeExplorerPath={(path, mode) => {
        history[mode](`/instance/snapshots/${explorerPathToString(path)}`);
      }}
    />
  );
};

export const PipelineExplorerContainer: React.FC<{
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  repoAddress?: RepoAddress;
  isGraph?: boolean;
}> = ({explorerPath, repoAddress, onChangeExplorerPath, isGraph = false}) => {
  const [options, setOptions] = React.useState<GraphExplorerOptions>({
    explodeComposites: false,
  });

  const parentNames = explorerPath.opNames.slice(0, explorerPath.opNames.length - 1);
  const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);
  const {flagAssetGraph} = useFeatureFlags();

  const pipelineResult = useQuery<PipelineExplorerRootQuery, PipelineExplorerRootQueryVariables>(
    PIPELINE_EXPLORER_ROOT_QUERY,
    {
      variables: {
        pipelineSelector: pipelineSelector,
        snapshotPipelineSelector: explorerPath.snapshotId ? undefined : pipelineSelector,
        snapshotId: explorerPath.snapshotId ? explorerPath.snapshotId : undefined,
        rootHandleID: parentNames.join('.'),
        requestScopeHandleID: options.explodeComposites ? undefined : parentNames.join('.'),
      },
    },
  );

  return (
    <Loading<PipelineExplorerRootQuery> queryResult={pipelineResult}>
      {({pipelineSnapshotOrError: result, assetNodes}) => {
        if (result.__typename !== 'PipelineSnapshot') {
          return <NonIdealPipelineQueryResult isGraph={isGraph} result={result} />;
        }

        const parentHandle = result.solidHandle;
        const displayedHandles = options.explodeComposites
          ? explodeCompositesInHandleGraph(result.solidHandles)
          : result.solidHandles;

        if (flagAssetGraph && assetNodes.length > 0) {
          const unrepresentedOps = result.solidHandles.filter(
            (handle) => !assetNodes.some((asset) => asset.opName === handle.handleID),
          );
          if (unrepresentedOps.length) {
            console.error(
              `The following ops are not represented in the ${
                explorerPath.pipelineName
              } asset graph: ${unrepresentedOps
                .map((h) => h.solid.name)
                .join(
                  ', ',
                )}. Does this graph have a mix of ops and assets? This isn't currently supported.`,
            );
          }
          return (
            <AssetGraphExplorer
              pipelineSelector={pipelineSelector}
              handles={displayedHandles}
              explorerPath={explorerPath}
              onChangeExplorerPath={onChangeExplorerPath}
            />
          );
        }

        return (
          <GraphExplorer
            options={options}
            setOptions={setOptions}
            explorerPath={explorerPath}
            onChangeExplorerPath={onChangeExplorerPath}
            pipelineOrGraph={result}
            repoAddress={repoAddress}
            handles={displayedHandles}
            parentHandle={parentHandle ? parentHandle : undefined}
            isGraph={isGraph}
            getInvocations={(definitionName) =>
              displayedHandles
                .filter((s) => s.solid.definition.name === definitionName)
                .map((s) => ({handleID: s.handleID}))
            }
          />
        );
      }}
    </Loading>
  );
};

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
  query PipelineExplorerRootQuery(
    $pipelineSelector: PipelineSelector!
    $snapshotPipelineSelector: PipelineSelector
    $snapshotId: String
    $rootHandleID: String!
    $requestScopeHandleID: String
  ) {
    assetNodes(pipeline: $pipelineSelector) {
      id
      opName
    }
    pipelineSnapshotOrError(
      snapshotId: $snapshotId
      activePipelineSelector: $snapshotPipelineSelector
    ) {
      ... on PipelineSnapshot {
        id
        name
        ...GraphExplorerFragment

        solidHandle(handleID: $rootHandleID) {
          ...GraphExplorerSolidHandleFragment
        }
        solidHandles(parentHandleID: $requestScopeHandleID) {
          handleID
          solid {
            name
          }
          ...GraphExplorerSolidHandleFragment
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineSnapshotNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }
  ${GRAPH_EXPLORER_FRAGMENT}
  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
`;
