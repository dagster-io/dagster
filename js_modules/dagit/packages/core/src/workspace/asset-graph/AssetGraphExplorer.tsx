import {gql, QueryResult, useQuery} from '@apollo/client';
import _, {uniq, without} from 'lodash';
import React from 'react';
import {useHistory} from 'react-router';
import styled from 'styled-components/macro';

import {filterByQuery} from '../../app/GraphQueryImpl';
import {QueryCountdown} from '../../app/QueryCountdown';
import {SVGViewport} from '../../graph/SVGViewport';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {RightInfoPanel, RightInfoPanelContent} from '../../pipelines/GraphExplorer';
import {EmptyDAGNotice, LargeDAGNotice} from '../../pipelines/GraphNotices';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {SidebarPipelineOrJobOverview} from '../../pipelines/SidebarPipelineOrJobOverview';
import {GraphExplorerSolidHandleFragment} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {useDidLaunchEvent} from '../../runs/RunUtils';
import {GraphQueryInput} from '../../ui/GraphQueryInput';
import {Loading} from '../../ui/Loading';
import {NonIdealState} from '../../ui/NonIdealState';
import {SplitPanelContainer} from '../../ui/SplitPanelContainer';
import {buildPipelineSelector} from '../WorkspaceContext';
import {RepoAddress} from '../types';

import {AssetLinks} from './AssetLinks';
import {AssetNode, ASSET_NODE_FRAGMENT, ASSET_NODE_LIVE_FRAGMENT} from './AssetNode';
import {ForeignNode} from './ForeignNode';
import {SidebarAssetInfo, SidebarAssetsInfo} from './SidebarAssetInfo';
import {
  buildGraphData,
  buildLiveData,
  GraphData,
  graphHasCycles,
  IN_PROGRESS_RUNS_FRAGMENT,
  layoutGraph,
  LiveData,
  Node,
} from './Utils';
import {AssetGraphLiveQuery, AssetGraphLiveQueryVariables} from './types/AssetGraphLiveQuery';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
  AssetGraphQuery_pipelineOrError_Pipeline_assetNodes,
} from './types/AssetGraphQuery';
import {useFindAssetInWorkspace} from './useFindAssetInWorkspace';

type AssetNode = AssetGraphQuery_pipelineOrError_Pipeline_assetNodes;

interface Props {
  repoAddress: RepoAddress;
  explorerPath: ExplorerPath;
  handles: GraphExplorerSolidHandleFragment[];
  selectedHandles: GraphExplorerSolidHandleFragment[];
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
}

export const AssetGraphExplorer: React.FC<Props> = (props) => {
  const {repoAddress, explorerPath, handles} = props;
  const pipelineSelector = buildPipelineSelector(repoAddress || null, explorerPath.pipelineName);
  const repositorySelector = {
    repositoryLocationName: repoAddress.location,
    repositoryName: repoAddress.name,
  };

  const queryResult = useQuery<AssetGraphQuery, AssetGraphQueryVariables>(ASSETS_GRAPH_QUERY, {
    variables: {pipelineSelector},
    notifyOnNetworkStatusChange: true,
  });

  const {graphData, graphAssetKeys} = React.useMemo(() => {
    if (queryResult.data?.pipelineOrError.__typename !== 'Pipeline') {
      return {graphAssetKeys: [], graphData: null};
    }
    const assetNodes = queryResult.data.pipelineOrError.assetNodes;
    const queryOps = filterByQuery(
      handles.map((h) => h.solid),
      explorerPath.opsQuery,
    );
    const queryAssetNodes = assetNodes.filter((a) =>
      queryOps.all.some((op) => op.name === a.opName),
    );
    const graphData = buildGraphData(queryAssetNodes);
    return {
      graphAssetKeys: queryAssetNodes.map((n) => ({path: n.assetKey.path})),
      graphData: graphData,
    };
  }, [queryResult.data, handles, explorerPath.opsQuery]);

  const liveResult = useQuery<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>(
    ASSETS_GRAPH_LIVE_QUERY,
    {
      skip: graphAssetKeys.length === 0,
      variables: {pipelineSelector, repositorySelector, assetKeys: graphAssetKeys},
      notifyOnNetworkStatusChange: true,
      pollInterval: 5 * 1000,
    },
  );

  const liveDataByNode = React.useMemo(() => {
    if (!liveResult.data || !graphData) {
      return {};
    }

    const {repositoryOrError, pipelineOrError} = liveResult.data;
    const liveAssetNodes =
      pipelineOrError.__typename === 'Pipeline' ? pipelineOrError.assetNodes : [];
    const inProgressRunsByStep =
      repositoryOrError.__typename === 'Repository' ? repositoryOrError.inProgressRunsByStep : [];

    return buildLiveData(graphData, liveAssetNodes, inProgressRunsByStep);
  }, [graphData, liveResult]);

  useDocumentTitle('Assets');
  useDidLaunchEvent(liveResult.refetch);

  return (
    <Loading allowStaleData queryResult={queryResult}>
      {() => {
        if (!graphData) {
          return <NonIdealState icon="error" title="Query Error" />;
        }

        const hasCycles = graphHasCycles(graphData);

        if (hasCycles) {
          return (
            <NonIdealState
              icon="error"
              title="Cycle detected"
              description="Assets dependencies form a cycle"
            />
          );
        }

        return (
          <AssetGraphExplorerWithData
            key={explorerPath.pipelineName}
            graphData={graphData}
            liveDataQueryResult={liveResult}
            liveDataByNode={liveDataByNode}
            {...props}
          />
        );
      }}
    </Loading>
  );
};

const AssetGraphExplorerWithData: React.FC<
  {
    graphData: GraphData;
    liveDataByNode: LiveData;
    liveDataQueryResult: QueryResult<any>;
  } & Props
> = (props) => {
  const {
    repoAddress,
    handles,
    selectedHandles,
    explorerPath,
    onChangeExplorerPath,
    liveDataQueryResult,
    liveDataByNode,
    graphData,
  } = props;

  const history = useHistory();
  const findAssetInWorkspace = useFindAssetInWorkspace();

  const selectedDefinitions = selectedHandles.map((h) => h.solid.definition);
  const selectedGraphNodes = selectedDefinitions.map(
    (def) => Object.values(graphData.nodes).find((node) => node.definition.opName === def.name)!,
  );
  const focusedGraphNode = selectedGraphNodes[selectedGraphNodes.length - 1];

  const onSelectNode = React.useCallback(
    async (e: React.MouseEvent<any>, assetKey: {path: string[]}, node: Node | null) => {
      e.stopPropagation();

      let clicked: {opName: string | null; jobName: string | null} = {opName: null, jobName: null};

      if (node?.definition) {
        // The asset's defintion was provided in our job.assetNodes query. Show it in the current graph.
        clicked = {opName: node.definition.opName, jobName: explorerPath.pipelineName};
      } else {
        // The asset's definition was not provided in our query for job.assetNodes. This means
        // it's in another job or is a foreign asset not defined in the repository at all.
        clicked = await findAssetInWorkspace(assetKey);
      }

      if (!clicked.opName || !clicked.jobName) {
        // We were unable to find this asset in the workspace - show it in the asset catalog.
        history.push(`/instance/assets/${assetKey.path.join('/')}`);
        return;
      }

      let nextOpsQuery = explorerPath.opsQuery;
      let nextOpsNameSelection = clicked.opName;

      if (clicked.jobName !== explorerPath.pipelineName) {
        nextOpsQuery = '';
      } else if (e.shiftKey || e.metaKey) {
        const existing = explorerPath.opNames[0].split(',');
        const added =
          e.shiftKey && focusedGraphNode && node
            ? opsInRange({graph: graphData, from: focusedGraphNode, to: node})
            : [clicked.opName];

        nextOpsNameSelection = (existing.includes(clicked.opName)
          ? without(existing, clicked.opName)
          : uniq([...existing, ...added])
        ).join(',');
      }

      onChangeExplorerPath(
        {
          ...explorerPath,
          opNames: [nextOpsNameSelection],
          opsQuery: nextOpsQuery,
          pipelineName: clicked.jobName,
        },
        'replace',
      );
    },
    [
      explorerPath,
      onChangeExplorerPath,
      findAssetInWorkspace,
      history,
      focusedGraphNode,
      graphData,
    ],
  );

  const queryResultAssets = React.useMemo(
    () =>
      filterByQuery(
        handles.map((h) => h.solid),
        explorerPath.opsQuery,
      ),
    [explorerPath.opsQuery, handles],
  );

  const layout = React.useMemo(() => layoutGraph(graphData), [graphData]);

  const viewportEl = React.useRef<SVGViewport>();
  React.useEffect(() => {
    viewportEl.current?.autocenter();
  }, [layout, viewportEl]);

  return (
    <SplitPanelContainer
      identifier="explorer"
      firstInitialPercent={70}
      firstMinSize={600}
      first={
        <>
          <SVGViewport
            ref={(r) => (viewportEl.current = r || undefined)}
            interactor={SVGViewport.Interactors.PanAndZoom}
            graphWidth={layout.width}
            graphHeight={layout.height}
            onKeyDown={() => {}}
            onClick={() =>
              onChangeExplorerPath(
                {...explorerPath, pipelineName: explorerPath.pipelineName, opNames: []},
                'replace',
              )
            }
            maxZoom={1.2}
            maxAutocenterZoom={1.0}
          >
            {({scale: _scale}, bounds) => (
              <SVGContainer width={layout.width} height={layout.height}>
                <AssetLinks edges={layout.edges} />

                {layout.nodes.map((layoutNode) => {
                  const graphNode = graphData.nodes[layoutNode.id];
                  const path = JSON.parse(layoutNode.id);
                  if (
                    layoutNode.x + layoutNode.width < bounds.left ||
                    layoutNode.y + layoutNode.height < bounds.top ||
                    layoutNode.x > bounds.right ||
                    layoutNode.y > bounds.bottom
                  ) {
                    return null;
                  }

                  return (
                    <foreignObject
                      {...layoutNode}
                      key={layoutNode.id}
                      onClick={(e) => onSelectNode(e, {path}, graphNode)}
                      style={{overflow: 'visible'}}
                    >
                      {!graphNode || !graphNode.definition.opName ? (
                        <ForeignNode assetKey={{path}} />
                      ) : (
                        <AssetNode
                          definition={graphNode.definition}
                          liveData={liveDataByNode[graphNode.id]}
                          metadata={
                            handles.find((h) => h.handleID === graphNode.definition.opName)!.solid
                              .definition.metadata
                          }
                          selected={focusedGraphNode === graphNode}
                          jobName={explorerPath.pipelineName}
                          repoAddress={repoAddress}
                          secondaryHighlight={selectedGraphNodes.includes(graphNode)}
                        />
                      )}
                    </foreignObject>
                  );
                })}
              </SVGContainer>
            )}
          </SVGViewport>

          {handles.length === 0 ? (
            <EmptyDAGNotice nodeType="asset" isGraph />
          ) : queryResultAssets.applyingEmptyDefault ? (
            <LargeDAGNotice nodeType="asset" />
          ) : undefined}

          <div style={{position: 'absolute', right: 8, top: 6}}>
            <QueryCountdown pollInterval={5 * 1000} queryResult={liveDataQueryResult} />
          </div>
          <AssetQueryInputContainer>
            <GraphQueryInput
              items={handles.map((h) => h.solid)}
              value={explorerPath.opsQuery}
              placeholder="Type an asset subset…"
              onChange={(opsQuery) => onChangeExplorerPath({...explorerPath, opsQuery}, 'replace')}
            />
          </AssetQueryInputContainer>
        </>
      }
      second={
        <RightInfoPanel>
          <RightInfoPanelContent>
            {selectedGraphNodes.length > 1 ? (
              <SidebarAssetsInfo
                jobName={explorerPath.pipelineName}
                nodes={selectedGraphNodes.map((n) => n.definition)}
                repoAddress={repoAddress}
              />
            ) : selectedGraphNodes.length === 1 && selectedGraphNodes[0] ? (
              <SidebarAssetInfo
                jobName={explorerPath.pipelineName}
                node={selectedGraphNodes[0].definition}
                liveData={liveDataByNode[selectedGraphNodes[0].id]}
                definition={selectedDefinitions[0]}
                repoAddress={repoAddress}
              />
            ) : (
              <SidebarPipelineOrJobOverview repoAddress={repoAddress} explorerPath={explorerPath} />
            )}
          </RightInfoPanelContent>
        </RightInfoPanel>
      }
    />
  );
};

const ASSETS_GRAPH_LIVE_QUERY = gql`
  query AssetGraphLiveQuery(
    $pipelineSelector: PipelineSelector!
    $repositorySelector: RepositorySelector!
    $assetKeys: [AssetKeyInput!]
  ) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        name
        inProgressRunsByStep {
          ...InProgressRunsFragment
        }
      }
    }
    pipelineOrError(params: $pipelineSelector) {
      ... on Pipeline {
        id
        assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
          id
          ...AssetNodeLiveFragment
        }
      }
    }
  }
  ${IN_PROGRESS_RUNS_FRAGMENT}
  ${ASSET_NODE_LIVE_FRAGMENT}
`;

const ASSETS_GRAPH_QUERY = gql`
  query AssetGraphQuery($pipelineSelector: PipelineSelector!) {
    pipelineOrError(params: $pipelineSelector) {
      ... on Pipeline {
        id
        assetNodes {
          id
          ...AssetNodeFragment
          dependencyKeys {
            path
          }
        }
      }
    }
  }
  ${ASSET_NODE_FRAGMENT}
`;

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;

const AssetQueryInputContainer = styled.div`
  z-index: 2;
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  display: flex;
`;

const graphDirectionOf = ({graph, from, to}: {graph: GraphData; from: Node; to: Node}) => {
  const stack = [from];
  while (stack.length) {
    const node = stack.pop()!;

    const downstream = [...Object.keys(graph.downstream[node.id] || {})]
      .map((n) => graph.nodes[n])
      .filter(Boolean);
    if (downstream.some((d) => d.id === to.id)) {
      return 'downstream';
    }
    stack.push(...downstream);
  }
  return 'upstream';
};

const opsInRange = (
  {graph, from, to}: {graph: GraphData; from: Node; to: Node},
  seen: string[] = [],
) => {
  if (!from) {
    return [];
  }
  if (from.id === to.id) {
    return [to.definition.opName!];
  }

  if (seen.length === 0 && graphDirectionOf({graph, from, to}) === 'upstream') {
    [from, to] = [to, from];
  }

  const downstream = [...Object.keys(graph.downstream[from.id] || {})]
    .map((n) => graph.nodes[n])
    .filter(Boolean);

  const ledToTarget: string[] = [];

  for (const node of downstream) {
    if (seen.includes(node.id)) {
      continue;
    }
    const result: string[] = opsInRange({graph, from: node, to}, [...seen, from.id]);
    if (result.length) {
      ledToTarget.push(from.definition.opName!, ...result);
    }
  }
  return uniq(ledToTarget);
};
