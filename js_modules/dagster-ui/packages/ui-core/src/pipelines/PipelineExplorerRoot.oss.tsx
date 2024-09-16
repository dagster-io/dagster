import {useState} from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {explodeCompositesInHandleGraph} from './CompositeSupport';
import {
  GRAPH_EXPLORER_ASSET_NODE_FRAGMENT,
  GRAPH_EXPLORER_FRAGMENT,
  GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT,
  GraphExplorer,
  GraphExplorerOptions,
} from './GraphExplorer';
import {NonIdealPipelineQueryResult} from './NonIdealPipelineQueryResult';
import {ExplorerPath, explorerPathFromString, explorerPathToString} from './PipelinePathUtils';
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQueryVariables,
} from './types/PipelineExplorerRoot.oss.types';
import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {useTrackPageView} from '../app/analytics';
import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphViewType} from '../asset-graph/Utils';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntryFragment';
import {Loading} from '../ui/Loading';
import {buildPipelineSelector} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

export const PipelineExplorerSnapshotRoot = () => {
  useTrackPageView();

  const params = useParams();
  const explorerPath = explorerPathFromString((params as any)['0']);
  const {pipelineName, snapshotId} = explorerPath;
  const history = useHistory();

  useDocumentTitle(`Snapshot: ${pipelineName}${snapshotId ? `@${snapshotId.slice(0, 8)}` : ''}`);

  return (
    <PipelineExplorerContainer
      explorerPath={explorerPath}
      onChangeExplorerPath={(path, mode) => {
        history[mode](`/snapshots/${explorerPathToString(path)}`);
      }}
      onNavigateToSourceAssetNode={(e, {assetKey}) => {
        const path = assetDetailsPathForKey(assetKey);
        if (e.metaKey) {
          window.open(path, '_blank');
        } else {
          history.push(assetDetailsPathForKey(assetKey));
        }
      }}
    />
  );
};

export const PipelineExplorerContainer = ({
  explorerPath,
  repoAddress,
  onChangeExplorerPath,
  onNavigateToSourceAssetNode,
  isGraph = false,
}: {
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  onNavigateToSourceAssetNode: (
    e: Pick<React.MouseEvent<any>, 'metaKey'>,
    node: AssetLocation,
  ) => void;
  repoAddress?: RepoAddress;
  isGraph?: boolean;
}) => {
  const [options, setOptions] = useState<GraphExplorerOptions>({
    explodeComposites: explorerPath.explodeComposites ?? false,
    preferAssetRendering: true,
  });

  const parentNames = explorerPath.opNames.slice(0, explorerPath.opNames.length - 1);
  const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);

  const pipelineResult = useQuery<PipelineExplorerRootQuery, PipelineExplorerRootQueryVariables>(
    PIPELINE_EXPLORER_ROOT_QUERY,
    {
      variables: {
        snapshotPipelineSelector: explorerPath.snapshotId ? undefined : pipelineSelector,
        snapshotId: explorerPath.snapshotId ? explorerPath.snapshotId : undefined,
        rootHandleID: parentNames.join('.'),
        requestScopeHandleID: options.explodeComposites ? undefined : parentNames.join('.'),
      },
    },
  );

  return (
    <Loading<PipelineExplorerRootQuery> queryResult={pipelineResult}>
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
              viewType={AssetGraphViewType.JOB}
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

export const PIPELINE_EXPLORER_ROOT_QUERY = gql`
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
        ...GraphExplorerFragment
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

  ${METADATA_ENTRY_FRAGMENT}
  ${GRAPH_EXPLORER_FRAGMENT}
  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
  ${GRAPH_EXPLORER_ASSET_NODE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
