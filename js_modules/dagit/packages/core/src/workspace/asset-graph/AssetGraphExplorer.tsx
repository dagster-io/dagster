import {gql, QueryResult, useQuery} from '@apollo/client';
import {Box, ColorsWIP, IconWIP, NonIdealState, SplitPanelContainer} from '@dagster-io/ui';
import _, {uniq, without} from 'lodash';
import React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {filterByQuery, GraphQueryItem} from '../../app/GraphQueryImpl';
import {QueryCountdown} from '../../app/QueryCountdown';
import {tokenForAssetKey} from '../../app/Util';
import {SVGViewport} from '../../graph/SVGViewport';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {RightInfoPanel, RightInfoPanelContent} from '../../pipelines/GraphExplorer';
import {EmptyDAGNotice, LargeDAGNotice} from '../../pipelines/GraphNotices';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {SidebarPipelineOrJobOverview} from '../../pipelines/SidebarPipelineOrJobOverview';
import {GraphExplorerSolidHandleFragment} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {useDidLaunchEvent} from '../../runs/RunUtils';
import {PipelineSelector} from '../../types/globalTypes';
import {GraphQueryInput} from '../../ui/GraphQueryInput';
import {Loading} from '../../ui/Loading';

import {AssetLinks} from './AssetLinks';
import {AssetNode, ASSET_NODE_FRAGMENT, ASSET_NODE_LIVE_FRAGMENT} from './AssetNode';
import {ForeignNode} from './ForeignNode';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {SidebarAssetInfo} from './SidebarAssetInfo';
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
  AssetGraphQuery_assetNodes,
} from './types/AssetGraphQuery';
import {useFindAssetInWorkspace} from './useFindAssetInWorkspace';

type AssetNode = AssetGraphQuery_assetNodes;

interface Props {
  pipelineSelector?: PipelineSelector;
  handles?: GraphExplorerSolidHandleFragment[];

  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
}

function buildGraphQueryItems(nodes: AssetNode[]) {
  const items: {
    [name: string]: GraphQueryItem & {
      node: AssetNode;
    };
  } = {};

  for (const node of nodes) {
    const name = tokenForAssetKey(node.assetKey);
    items[name] = {
      node: node,
      name: name,
      inputs: node.dependencyKeys.map((key) => ({
        dependsOn: [{solid: {name: tokenForAssetKey(key)}}],
      })),
      outputs: node.dependedByKeys.map((key) => ({
        dependedBy: [{solid: {name: tokenForAssetKey(key)}}],
      })),
    };
  }
  return Object.values(items);
}

export const AssetGraphExplorer: React.FC<Props> = (props) => {
  const {pipelineSelector, explorerPath} = props;

  const queryResult = useQuery<AssetGraphQuery, AssetGraphQueryVariables>(ASSETS_GRAPH_QUERY, {
    variables: {pipelineSelector},
    notifyOnNetworkStatusChange: true,
  });

  const {
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    applyingEmptyDefault,
  } = React.useMemo(() => {
    if (queryResult.data?.assetNodes === undefined) {
      return {
        graphAssetKeys: [],
        graphQueryItems: [],
        assetGraphData: null,
        applyingEmptyDefault: false,
      };
    }
    const graphQueryItems = buildGraphQueryItems(queryResult.data.assetNodes);
    const {all, applyingEmptyDefault} = filterByQuery(graphQueryItems, explorerPath.opsQuery);

    return {
      graphAssetKeys: all.map((n) => ({path: n.node.assetKey.path})),
      assetGraphData: buildGraphData(all.map((n) => n.node)),
      graphQueryItems,
      applyingEmptyDefault,
    };
  }, [queryResult.data, explorerPath.opsQuery]);

  const liveResult = useQuery<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>(
    ASSETS_GRAPH_LIVE_QUERY,
    {
      skip: graphAssetKeys.length === 0,
      variables: {
        assetKeys: graphAssetKeys,
        repositorySelector: {
          repositoryLocationName: pipelineSelector?.repositoryLocationName || '',
          repositoryName: pipelineSelector?.repositoryName || '',
        },
      },
      notifyOnNetworkStatusChange: true,
      pollInterval: 5 * 1000,
    },
  );

  const liveDataByNode = React.useMemo(() => {
    if (!liveResult.data || !assetGraphData) {
      return {};
    }

    const {repositoryOrError, assetNodes: liveAssetNodes} = liveResult.data;
    const inProgressRunsByStep =
      repositoryOrError.__typename === 'Repository' ? repositoryOrError.inProgressRunsByStep : [];

    return buildLiveData(assetGraphData, liveAssetNodes, inProgressRunsByStep);
  }, [assetGraphData, liveResult]);

  useDocumentTitle('Assets');
  useDidLaunchEvent(liveResult.refetch);

  return (
    <Loading allowStaleData queryResult={queryResult}>
      {() => {
        if (!assetGraphData) {
          return <NonIdealState icon="error" title="Query Error" />;
        }

        const hasCycles = graphHasCycles(assetGraphData);

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
            assetGraphData={assetGraphData}
            graphQueryItems={graphQueryItems}
            applyingEmptyDefault={applyingEmptyDefault}
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
    assetGraphData: GraphData;
    graphQueryItems: GraphQueryItem[];
    liveDataByNode: LiveData;
    liveDataQueryResult: QueryResult<any>;
    applyingEmptyDefault: boolean;
  } & Props
> = (props) => {
  const {
    handles = [],
    explorerPath,
    onChangeExplorerPath,
    liveDataQueryResult,
    liveDataByNode,
    assetGraphData,
    graphQueryItems,
    applyingEmptyDefault,
    pipelineSelector,
  } = props;

  const history = useHistory();
  const findAssetInWorkspace = useFindAssetInWorkspace();

  const selectedAssetValues = explorerPath.opNames[explorerPath.opNames.length - 1].split(',');
  const selectedGraphNodes = Object.values(assetGraphData.nodes).filter((node) =>
    selectedAssetValues.includes(tokenForAssetKey(node.definition.assetKey)),
  );
  const lastSelectedNode = selectedGraphNodes[selectedGraphNodes.length - 1];
  const launchGraphNodes = selectedGraphNodes.length
    ? selectedGraphNodes
    : Object.values(assetGraphData.nodes);

  const onSelectNode = React.useCallback(
    async (e: React.MouseEvent<any>, assetKey: {path: string[]}, node: Node | null) => {
      e.stopPropagation();

      const token = tokenForAssetKey(assetKey);
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
      let nextOpsNameSelection = token;

      if (clicked.jobName !== explorerPath.pipelineName) {
        nextOpsQuery = '';
      } else if (e.shiftKey || e.metaKey) {
        const existing = explorerPath.opNames[0].split(',');
        const added =
          e.shiftKey && lastSelectedNode && node
            ? opsInRange({graph: assetGraphData, from: lastSelectedNode, to: node})
            : [token];

        nextOpsNameSelection = (existing.includes(token)
          ? without(existing, token)
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
      lastSelectedNode,
      assetGraphData,
    ],
  );

  const layout = React.useMemo(() => layoutGraph(assetGraphData), [assetGraphData]);

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
                  const graphNode = assetGraphData.nodes[layoutNode.id];
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
                            handles.find((h) => h.handleID === graphNode.definition.opName)?.solid
                              .definition.metadata || []
                          }
                          selected={selectedGraphNodes.includes(graphNode)}
                          jobName={explorerPath.pipelineName}
                        />
                      )}
                    </foreignObject>
                  );
                })}
              </SVGContainer>
            )}
          </SVGViewport>

          {Object.keys(assetGraphData.nodes).length === 0 ? (
            <EmptyDAGNotice nodeType="asset" isGraph />
          ) : applyingEmptyDefault ? (
            <LargeDAGNotice nodeType="asset" />
          ) : undefined}

          <div style={{position: 'absolute', right: 12, top: 12}}>
            <LaunchAssetExecutionButton
              title={titleForLaunch(selectedGraphNodes, liveDataByNode)}
              preferredJobName={explorerPath.pipelineName}
              assets={launchGraphNodes.map((n) => n.definition)}
            />
          </div>
          <div style={{position: 'absolute', left: 24, top: 16}}>
            <QueryCountdown pollInterval={5 * 1000} queryResult={liveDataQueryResult} />
          </div>
          <AssetQueryInputContainer>
            <GraphQueryInput
              items={graphQueryItems}
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
              <Box
                style={{height: '70%', color: ColorsWIP.Gray400}}
                flex={{justifyContent: 'center', alignItems: 'center', gap: 4, direction: 'column'}}
              >
                <IconWIP size={48} name="asset" color={ColorsWIP.Gray400} />
                {`${selectedGraphNodes.length} Assets Selected`}
              </Box>
            ) : selectedGraphNodes.length === 1 && selectedGraphNodes[0] ? (
              <SidebarAssetInfo
                node={selectedGraphNodes[0].definition}
                liveData={liveDataByNode[selectedGraphNodes[0].id]}
                definition={
                  handles.find(
                    (h) => h.solid.definition.name === selectedGraphNodes[0].definition.opName,
                  )?.solid.definition
                }
              />
            ) : pipelineSelector ? (
              <SidebarPipelineOrJobOverview pipelineSelector={pipelineSelector} />
            ) : undefined}
          </RightInfoPanelContent>
        </RightInfoPanel>
      }
    />
  );
};

const ASSETS_GRAPH_LIVE_QUERY = gql`
  query AssetGraphLiveQuery(
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
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      ...AssetNodeLiveFragment
    }
  }
  ${IN_PROGRESS_RUNS_FRAGMENT}
  ${ASSET_NODE_LIVE_FRAGMENT}
`;

const ASSETS_GRAPH_QUERY = gql`
  query AssetGraphQuery($pipelineSelector: PipelineSelector) {
    assetNodes(pipeline: $pipelineSelector) {
      id
      ...AssetNodeFragment
      jobNames
      dependencyKeys {
        path
      }
      dependedByKeys {
        path
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

const titleForLaunch = (nodes: Node[], liveDataByNode: LiveData) => {
  const isRematerializeForAll = (nodes.length
    ? nodes.map((n) => liveDataByNode[n.id])
    : Object.values(liveDataByNode)
  ).every((e) => !!e?.lastMaterialization);

  return `${isRematerializeForAll ? 'Rematerialize' : 'Materialize'} ${
    nodes.length === 0 ? `All` : nodes.length === 1 ? `Selected` : `Selected (${nodes.length})`
  }`;
};
