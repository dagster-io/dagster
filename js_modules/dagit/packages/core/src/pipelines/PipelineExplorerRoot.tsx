import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {RouteComponentProps, useHistory} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Loading} from '../ui/Loading';
import {NonIdealState} from '../ui/NonIdealState';
import {buildPipelineSelector} from '../workspace/WorkspaceContext';
import {AssetGraphExplorer} from '../workspace/asset-graph/AssetGraphExplorer';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {explodeCompositesInHandleGraph} from './CompositeSupport';
import {NonIdealPipelineQueryResult} from './NonIdealPipelineQueryResult';
import {
  GraphExplorer,
  GraphExplorerOptions,
  GRAPH_EXPLORER_FRAGMENT,
  GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT,
} from './GraphExplorer';
import {
  PipelineExplorerPath,
  explorerPathFromString,
  explorerPathToString,
} from './PipelinePathUtils';
import {
  GraphExplorerRootQuery,
  GraphExplorerRootQueryVariables,
} from './types/GraphExplorerRootQuery';
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQueryVariables,
} from './types/PipelineExplorerRootQuery';

export const GraphExplorerRoot: React.FC<RouteComponentProps & {repoAddress: RepoAddress}> = (
  props,
) => {
  const explorerPath = explorerPathFromString(props.match.params['0']);
  const {repoAddress} = props;
  const history = useHistory();
  const [options, setOptions] = React.useState<GraphExplorerOptions>({
    explodeComposites: false,
  });

  const selectedName = explorerPath.pathSolids[explorerPath.pathSolids.length - 1];
  const parentNames = explorerPath.pathSolids.slice(0, explorerPath.pathSolids.length - 1);
  const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);

  useDocumentTitle(`Graph: ${explorerPath.pipelineName}`);

  const graphResult = useQuery<GraphExplorerRootQuery, GraphExplorerRootQueryVariables>(
    GRAPH_EXPLORER_ROOT_QUERY,
    {
      variables: {
        graphSelector: {
          repositoryName: pipelineSelector.repositoryName,
          repositoryLocationName: pipelineSelector.repositoryLocationName,
          graphName: explorerPath.pipelineName,
        },
        rootHandleID: parentNames.join('.'),
        requestScopeHandleID: options.explodeComposites ? undefined : parentNames.join('.'),
      },
    },
  );

  return (
    <Loading<GraphExplorerRootQuery> queryResult={graphResult}>
      {({graphOrError: result}) => {
        if (result.__typename === 'GraphNotFoundError') {
          return (
            <NonIdealState icon="error" title={'Graph not found'} description={result.message} />
          );
        }
        if (result.__typename === 'PythonError') {
          return <NonIdealState icon="error" title="Query Error" description={result.message} />;
        }
        const parentHandle = result.solidHandle;
        const displayedHandles = options.explodeComposites
          ? explodeCompositesInHandleGraph(result.solidHandles)
          : result.solidHandles;

        const selectedHandle = displayedHandles.find((h) => h.solid.name === selectedName);
        return (
          <GraphExplorer
            options={options}
            setOptions={setOptions}
            explorerPath={explorerPath}
            onChangeExplorerPath={(path, mode) => {
              const fullPath = workspacePathFromAddress(
                props.repoAddress,
                `/graphs/${explorerPathToString(path)}`,
              );
              if (mode === 'push') {
                history.push(fullPath);
              } else {
                history.replace(fullPath);
              }
            }}
            pipeline={result}
            repoAddress={repoAddress}
            handles={displayedHandles}
            parentHandle={parentHandle ? parentHandle : undefined}
            selectedHandle={selectedHandle}
            isGraph={true}
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

export const PipelineExplorerSnapshotRoot: React.FC<RouteComponentProps> = (props) => {
  const explorerPath = explorerPathFromString(props.match.params['0']);
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
  explorerPath: PipelineExplorerPath;
  onChangeExplorerPath: (path: PipelineExplorerPath, mode: 'replace' | 'push') => void;
  repoAddress?: RepoAddress;
  isGraph?: boolean;
}> = ({explorerPath, repoAddress, onChangeExplorerPath, isGraph = false}) => {
  const [options, setOptions] = React.useState<GraphExplorerOptions>({
    explodeComposites: false,
  });

  const selectedName = explorerPath.pathSolids[explorerPath.pathSolids.length - 1];
  const parentNames = explorerPath.pathSolids.slice(0, explorerPath.pathSolids.length - 1);
  const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);
  const {flagAssetGraph} = useFeatureFlags();

  const pipelineResult = useQuery<PipelineExplorerRootQuery, PipelineExplorerRootQueryVariables>(
    PIPELINE_EXPLORER_ROOT_QUERY,
    {
      variables: {
        pipelineSelector: explorerPath.snapshotId ? undefined : pipelineSelector,
        snapshotId: explorerPath.snapshotId ? explorerPath.snapshotId : undefined,
        rootHandleID: parentNames.join('.'),
        requestScopeHandleID: options.explodeComposites ? undefined : parentNames.join('.'),
        repositorySelector: {
          repositoryName: pipelineSelector.repositoryName,
          repositoryLocationName: pipelineSelector.repositoryLocationName,
        },
      },
    },
  );

  return (
    <Loading<PipelineExplorerRootQuery> queryResult={pipelineResult}>
      {({pipelineSnapshotOrError: result, repositoryOrError}) => {
        if (result.__typename !== 'PipelineSnapshot') {
          return <NonIdealPipelineQueryResult isGraph={isGraph} result={result} />;
        }
        if (repositoryOrError.__typename !== 'Repository' && !explorerPath.snapshotId) {
          return <NonIdealPipelineQueryResult isGraph={isGraph} result={repositoryOrError} />;
        }

        const parentHandle = result.solidHandle;
        const displayedHandles = options.explodeComposites
          ? explodeCompositesInHandleGraph(result.solidHandles)
          : result.solidHandles;

        const selectedHandle = displayedHandles.find((h) => h.solid.name === selectedName);

        // Run a few assertions on the state of the world and redirect the user
        // back to safety if they've landed in an invalid place. Note that we can
        // pop one layer at a time and this renders recursively until we reach a
        // valid parent.
        const invalidSelection = selectedName && !selectedHandle;
        const invalidParent =
          parentHandle && parentHandle.solid.definition.__typename !== 'CompositeSolidDefinition';

        if (invalidSelection || invalidParent) {
          onChangeExplorerPath(
            {
              ...explorerPath,
              pathSolids: explorerPath.pathSolids.slice(0, explorerPath.pathSolids.length - 1),
            },
            'replace',
          );
        }

        const repositoryAssets =
          repositoryOrError.__typename === 'Repository' ? repositoryOrError.assetNodes : [];
        const isAssetGraph = result.solidHandles.some((handle) =>
          repositoryAssets.some(
            (asset) =>
              asset.opName === handle.handleID && asset.jobName === explorerPath.pipelineName,
          ),
        );

        if (flagAssetGraph && isAssetGraph) {
          const unrepresentedSolids = result.solidHandles.filter(
            (handle) =>
              !repositoryAssets.some(
                (asset) =>
                  asset.opName === handle.handleID && asset.jobName === explorerPath.pipelineName,
              ),
          );
          if (unrepresentedSolids.length) {
            console.error(
              `The following ops are not represented in the ${
                explorerPath.pipelineName
              } asset graph: ${unrepresentedSolids.map((h) => h.solid.name).join(', ')}`,
            );
          }
          return (
            <AssetGraphExplorer
              repoAddress={repoAddress!}
              handles={displayedHandles}
              selectedHandle={selectedHandle}
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
            pipeline={result}
            repoAddress={repoAddress}
            handles={displayedHandles}
            parentHandle={parentHandle ? parentHandle : undefined}
            selectedHandle={selectedHandle}
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
    $repositorySelector: RepositorySelector!
    $pipelineSelector: PipelineSelector
    $snapshotId: String
    $rootHandleID: String!
    $requestScopeHandleID: String
  ) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        assetNodes {
          id
          opName
          jobName
        }
      }
      ... on RepositoryNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
    }
    pipelineSnapshotOrError(snapshotId: $snapshotId, activePipelineSelector: $pipelineSelector) {
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

export const GRAPH_EXPLORER_ROOT_QUERY = gql`
  query GraphExplorerRootQuery(
    $graphSelector: GraphSelector
    $rootHandleID: String!
    $requestScopeHandleID: String
  ) {
    graphOrError(selector: $graphSelector) {
      ... on Graph {
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
      ... on GraphNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
  ${GRAPH_EXPLORER_FRAGMENT}
  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
`;
