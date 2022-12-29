import {useQuery} from '@apollo/client';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {useTrackPageView} from '../app/analytics';
import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {graphql} from '../graphql';
import {PipelineExplorerRootQueryQuery} from '../graphql/graphql';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Loading} from '../ui/Loading';
import {buildPipelineSelector} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {explodeCompositesInHandleGraph} from './CompositeSupport';
import {GraphExplorer, GraphExplorerOptions} from './GraphExplorer';
import {NonIdealPipelineQueryResult} from './NonIdealPipelineQueryResult';
import {ExplorerPath, explorerPathFromString, explorerPathToString} from './PipelinePathUtils';

export const PipelineExplorerSnapshotRoot = () => {
  useTrackPageView();

  const params = useParams();
  const explorerPath = explorerPathFromString(params['0']);
  const {pipelineName, snapshotId} = explorerPath;
  const history = useHistory();

  useDocumentTitle(`Snapshot: ${pipelineName}${snapshotId ? `@${snapshotId.slice(0, 8)}` : ''}`);

  return (
    <PipelineExplorerContainer
      explorerPath={explorerPath}
      onChangeExplorerPath={(path, mode) => {
        history[mode](`/snapshots/${explorerPathToString(path)}`);
      }}
      onNavigateToSourceAssetNode={({assetKey}) => {
        history.push(assetDetailsPathForKey(assetKey));
      }}
    />
  );
};

export const PipelineExplorerContainer: React.FC<{
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  onNavigateToSourceAssetNode: (node: AssetLocation) => void;
  repoAddress?: RepoAddress;
  isGraph?: boolean;
}> = ({
  explorerPath,
  repoAddress,
  onChangeExplorerPath,
  onNavigateToSourceAssetNode,
  isGraph = false,
}) => {
  const [options, setOptions] = React.useState<GraphExplorerOptions>({
    explodeComposites: explorerPath.explodeComposites ?? false,
    preferAssetRendering: true,
  });

  const parentNames = explorerPath.opNames.slice(0, explorerPath.opNames.length - 1);
  const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);

  const pipelineResult = useQuery(PIPELINE_EXPLORER_ROOT_QUERY, {
    variables: {
      snapshotPipelineSelector: explorerPath.snapshotId ? undefined : pipelineSelector,
      snapshotId: explorerPath.snapshotId ? explorerPath.snapshotId : undefined,
      rootHandleID: parentNames.join('.'),
      requestScopeHandleID: options.explodeComposites ? undefined : parentNames.join('.'),
    },
  });

  return (
    <Loading<PipelineExplorerRootQueryQuery> queryResult={pipelineResult}>
      {({pipelineSnapshotOrError: result}) => {
        if (result.__typename !== 'PipelineSnapshot') {
          return (
            <NonIdealPipelineQueryResult
              isGraph={isGraph}
              result={result}
              repoAddress={repoAddress}
            />
          );
        }

        const parentHandle = result.solidHandle;
        const displayedHandles = options.explodeComposites
          ? explodeCompositesInHandleGraph(result.solidHandles)
          : result.solidHandles;
        const assetNodesPresent = result.solidHandles.some(
          (h) => h.solid.definition.assetNodes.length > 0,
        );
        if (options.preferAssetRendering && assetNodesPresent) {
          return (
            <AssetGraphExplorer
              options={options}
              setOptions={setOptions}
              fetchOptions={{pipelineSelector}}
              explorerPath={explorerPath}
              onChangeExplorerPath={onChangeExplorerPath}
              onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
            />
          );
        }

        return (
          <GraphExplorer
            options={options}
            setOptions={setOptions}
            explorerPath={explorerPath}
            onChangeExplorerPath={onChangeExplorerPath}
            container={result}
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

export const PIPELINE_EXPLORER_ROOT_QUERY = graphql(`
  query PipelineExplorerRootQuery(
    $snapshotPipelineSelector: PipelineSelector
    $snapshotId: String
    $rootHandleID: String!
    $requestScopeHandleID: String
  ) {
    pipelineSnapshotOrError(
      snapshotId: $snapshotId
      activePipelineSelector: $snapshotPipelineSelector
    ) {
      ... on PipelineSnapshot {
        id
        name
        metadataEntries {
          ...MetadataEntryFragment
        }
        ...GraphExplorerFragment

        solidHandle(handleID: $rootHandleID) {
          ...GraphExplorerSolidHandleFragment
        }
        solidHandles(parentHandleID: $requestScopeHandleID) {
          handleID
          solid {
            name
            definition {
              assetNodes {
                id
                ...GraphExplorerAssetNodeFragment
              }
            }
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
      ...PythonErrorFragment
    }
  }
`);
