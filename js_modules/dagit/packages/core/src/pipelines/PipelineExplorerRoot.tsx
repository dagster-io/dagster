import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {RouteComponentProps, useHistory} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Loading} from '../ui/Loading';
import {usePipelineSelector} from '../workspace/WorkspaceContext';
import {AssetGraphExplorer} from '../workspace/asset-graph/AssetGraphExplorer';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {explodeCompositesInHandleGraph} from './CompositeSupport';
import {NonIdealPipelineQueryResult} from './NonIdealPipelineQueryResult';
import {
  PipelineExplorer,
  PipelineExplorerOptions,
  PIPELINE_EXPLORER_FRAGMENT,
  PIPELINE_EXPLORER_SOLID_HANDLE_FRAGMENT,
} from './PipelineExplorer';
import {
  PipelineExplorerPath,
  explorerPathFromString,
  explorerPathToString,
} from './PipelinePathUtils';
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQueryVariables,
} from './types/PipelineExplorerRootQuery';

export const PipelineExplorerRegexRoot: React.FC<
  RouteComponentProps & {repoAddress: RepoAddress}
> = (props) => {
  const explorerPath = explorerPathFromString(props.match.params['0']);
  const history = useHistory();

  useDocumentTitle(`Graph: ${explorerPath.pipelineName}`);

  return (
    <PipelineExplorerContainer
      explorerPath={explorerPath}
      repoAddress={props.repoAddress}
      isGraph
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
    />
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
  const [options, setOptions] = React.useState<PipelineExplorerOptions>({
    explodeComposites: false,
  });

  const selectedName = explorerPath.pathSolids[explorerPath.pathSolids.length - 1];
  const parentNames = explorerPath.pathSolids.slice(0, explorerPath.pathSolids.length - 1);
  const pipelineSelector = usePipelineSelector(repoAddress || null, explorerPath.pipelineName);
  const {flagAssetGraph} = useFeatureFlags();

  const queryResult = useQuery<PipelineExplorerRootQuery, PipelineExplorerRootQueryVariables>(
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
    <Loading<PipelineExplorerRootQuery> queryResult={queryResult}>
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
        const isAssetGraph = result.solidHandles.every((handle) =>
          repositoryAssets.some(
            (asset) =>
              asset.opName === handle.handleID && asset.jobName === explorerPath.pipelineName,
          ),
        );

        if (flagAssetGraph && isAssetGraph) {
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
          <PipelineExplorer
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
        ...PipelineExplorerFragment

        solidHandle(handleID: $rootHandleID) {
          ...PipelineExplorerSolidHandleFragment
        }
        solidHandles(parentHandleID: $requestScopeHandleID) {
          handleID
          solid {
            name
          }
          ...PipelineExplorerSolidHandleFragment
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
  ${PIPELINE_EXPLORER_FRAGMENT}
  ${PIPELINE_EXPLORER_SOLID_HANDLE_FRAGMENT}
`;
