import {gql, useQuery} from '@apollo/client';
import {Box, Checkbox, NonIdealState, SplitPanelContainer} from '@dagster-io/ui';
import _, {flatMap, uniq, uniqBy, without} from 'lodash';
import React from 'react';
import styled from 'styled-components/macro';

import {filterByQuery, GraphQueryItem} from '../../app/GraphQueryImpl';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  QueryRefreshState,
  useQueryRefreshAtInterval,
} from '../../app/QueryRefresh';
import {tokenForAssetKey} from '../../app/Util';
import {AssetKey} from '../../assets/types';
import {SVGViewport} from '../../graph/SVGViewport';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {
  GraphExplorerOptions,
  OptionsOverlay,
  QueryOverlay,
  RightInfoPanel,
  RightInfoPanelContent,
} from '../../pipelines/GraphExplorer';
import {
  EmptyDAGNotice,
  EntirelyFilteredDAGNotice,
  LargeDAGNotice,
} from '../../pipelines/GraphNotices';
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
import {OmittedAssetsNotice} from './OmittedAssetsNotice';
import {SidebarAssetInfo} from './SidebarAssetInfo';
import {
  buildGraphData,
  buildLiveData,
  GraphData,
  graphHasCycles,
  REPOSITORY_LIVE_FRAGMENT,
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
  options: GraphExplorerOptions;
  setOptions?: (options: GraphExplorerOptions) => void;

  pipelineSelector?: PipelineSelector;
  filterNodes?: (assetNode: AssetGraphQuery_assetNodes) => boolean;

  // Optionally pass op handles to display op metadata on the assets linked to each op.
  // (eg: the "ipynb" tag annotation). Right now, we already have this data loaded for
  // individual jobs, and the global asset graph quietly doesn't display these.
  handles?: GraphExplorerSolidHandleFragment[];

  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
}

export const AssetGraphExplorer: React.FC<Props> = (props) => {
  const {pipelineSelector, explorerPath} = props;

  const fetchResult = useQuery<AssetGraphQuery, AssetGraphQueryVariables>(ASSETS_GRAPH_QUERY, {
    variables: {pipelineSelector},
    notifyOnNetworkStatusChange: true,
  });

  const fetchResultFilteredNodes = React.useMemo(() => {
    const nodes = fetchResult.data?.assetNodes;
    if (!nodes) {
      return undefined;
    }
    return props.filterNodes ? nodes.filter(props.filterNodes) : nodes;
  }, [fetchResult.data, props.filterNodes]);

  const {
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    applyingEmptyDefault,
  } = React.useMemo(() => {
    if (fetchResultFilteredNodes === undefined) {
      return {
        graphAssetKeys: [],
        graphQueryItems: [],
        assetGraphData: null,
        applyingEmptyDefault: false,
      };
    }
    const graphQueryItems = buildGraphQueryItems(fetchResultFilteredNodes);
    const {all, applyingEmptyDefault} = filterByQuery(graphQueryItems, explorerPath.opsQuery);

    return {
      graphAssetKeys: all.map((n) => ({path: n.node.assetKey.path})),
      assetGraphData: buildGraphData(all.map((n) => n.node)),
      graphQueryItems,
      applyingEmptyDefault,
    };
  }, [fetchResultFilteredNodes, explorerPath.opsQuery]);

  const liveResult = useQuery<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>(
    ASSETS_GRAPH_LIVE_QUERY,
    {
      skip: graphAssetKeys.length === 0,
      variables: {
        assetKeys: graphAssetKeys,
        repositorySelector: pipelineSelector
          ? {
              repositoryLocationName: pipelineSelector.repositoryLocationName,
              repositoryName: pipelineSelector.repositoryName,
            }
          : undefined,
      },
      notifyOnNetworkStatusChange: true,
    },
  );

  const liveDataRefreshState = useQueryRefreshAtInterval(liveResult, FIFTEEN_SECONDS);

  const liveDataByNode = React.useMemo(() => {
    if (!liveResult.data || !assetGraphData) {
      return {};
    }

    const {repositoriesOrError, assetNodes: liveAssetNodes} = liveResult.data;
    const repos =
      repositoriesOrError.__typename === 'RepositoryConnection' ? repositoriesOrError.nodes : [];

    return buildLiveData(assetGraphData, liveAssetNodes, repos);
  }, [assetGraphData, liveResult]);

  useDocumentTitle('Assets');
  useDidLaunchEvent(liveResult.refetch);

  return (
    <Loading allowStaleData queryResult={fetchResult}>
      {() => {
        if (!assetGraphData) {
          return <NonIdealState icon="error" title="Query Error" />;
        }

        const hasCycles = graphHasCycles(assetGraphData);
        const assetKeys = fetchResult.data?.assetNodes.map((a) => a.assetKey) || [];

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
            assetKeys={assetKeys}
            assetGraphData={assetGraphData}
            graphQueryItems={graphQueryItems}
            applyingEmptyDefault={applyingEmptyDefault}
            liveDataRefreshState={liveDataRefreshState}
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
    assetKeys: AssetKey[];
    assetGraphData: GraphData;
    graphQueryItems: GraphQueryItem[];
    liveDataByNode: LiveData;
    liveDataRefreshState: QueryRefreshState;
    applyingEmptyDefault: boolean;
  } & Props
> = (props) => {
  const {
    handles = [],
    options,
    setOptions,
    explorerPath,
    onChangeExplorerPath,
    liveDataRefreshState,
    liveDataByNode,
    assetGraphData,
    graphQueryItems,
    applyingEmptyDefault,
    pipelineSelector,
  } = props;

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
        // it's in another job or is a source asset not defined in the repository at all.
        clicked = await findAssetInWorkspace(assetKey);
      }

      let nextOpsQuery = explorerPath.opsQuery;
      let nextOpsNameSelection = token;

      // If no opName, this is a source asset.
      if (clicked.jobName !== explorerPath.pipelineName || !clicked.opName) {
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
          pipelineName: clicked.jobName || explorerPath.pipelineName,
        },
        'replace',
      );
    },
    [explorerPath, onChangeExplorerPath, findAssetInWorkspace, lastSelectedNode, assetGraphData],
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
      firstMinSize={400}
      first={
        <>
          {graphQueryItems.length === 0 ? (
            <EmptyDAGNotice nodeType="asset" isGraph />
          ) : applyingEmptyDefault ? (
            <LargeDAGNotice nodeType="asset" />
          ) : Object.keys(assetGraphData.nodes).length === 0 ? (
            <EntirelyFilteredDAGNotice nodeType="asset" />
          ) : undefined}
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

                {layout.nodes.map((layoutNode, index) => {
                  const graphNode = assetGraphData.nodes[layoutNode.id];
                  const path = JSON.parse(layoutNode.id);

                  if (isNodeOffscreen(layoutNode, bounds)) {
                    return layoutNode.id === lastSelectedNode?.id ? (
                      <RecenterGraph
                        key={index}
                        viewportRef={viewportEl}
                        x={layoutNode.x + layoutNode.width / 2}
                        y={layoutNode.y + layoutNode.height / 2}
                      />
                    ) : null;
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

          {setOptions && (
            <OptionsOverlay>
              <Checkbox
                format="switch"
                label="View as Asset Graph"
                checked={options.preferAssetRendering}
                onChange={() => {
                  onChangeExplorerPath(
                    {
                      ...explorerPath,
                      opNames:
                        selectedGraphNodes.length && selectedGraphNodes[0].definition.opName
                          ? [selectedGraphNodes[0].definition.opName]
                          : [],
                    },
                    'replace',
                  );
                  setOptions({
                    ...options,
                    preferAssetRendering: !options.preferAssetRendering,
                  });
                }}
              />
            </OptionsOverlay>
          )}

          <Box
            flex={{direction: 'column', alignItems: 'flex-end', gap: 8}}
            style={{position: 'absolute', right: 12, top: 12}}
          >
            <Box flex={{alignItems: 'center', gap: 12}}>
              <QueryRefreshCountdown refreshState={liveDataRefreshState} />

              <LaunchAssetExecutionButton
                title={titleForLaunch(selectedGraphNodes, liveDataByNode)}
                preferredJobName={explorerPath.pipelineName}
                assets={launchGraphNodes.map((n) => n.definition)}
                upstreamAssetKeys={uniqBy(
                  flatMap(launchGraphNodes.map((n) => n.definition.dependencyKeys)),
                  (key) => JSON.stringify(key),
                ).filter(
                  (key) =>
                    !launchGraphNodes.some(
                      (n) => JSON.stringify(n.assetKey) === JSON.stringify(key),
                    ),
                )}
              />
            </Box>
            {!props.pipelineSelector && <OmittedAssetsNotice assetKeys={props.assetKeys} />}
          </Box>
          <QueryOverlay>
            <GraphQueryInput
              items={graphQueryItems}
              value={explorerPath.opsQuery}
              placeholder="Type an asset subset…"
              onChange={(opsQuery) => onChangeExplorerPath({...explorerPath, opsQuery}, 'replace')}
              popoverPosition="bottom-left"
            />
          </QueryOverlay>
        </>
      }
      second={
        selectedGraphNodes.length === 1 && selectedGraphNodes[0] ? (
          <RightInfoPanel>
            <RightInfoPanelContent>
              <SidebarAssetInfo
                assetKey={selectedGraphNodes[0].assetKey}
                liveData={liveDataByNode[selectedGraphNodes[0].id]}
              />
            </RightInfoPanelContent>
          </RightInfoPanel>
        ) : pipelineSelector ? (
          <RightInfoPanel>
            <RightInfoPanelContent>
              <SidebarPipelineOrJobOverview pipelineSelector={pipelineSelector} />
            </RightInfoPanelContent>
          </RightInfoPanel>
        ) : null
      }
    />
  );
};

const ASSETS_GRAPH_LIVE_QUERY = gql`
  query AssetGraphLiveQuery($repositorySelector: RepositorySelector, $assetKeys: [AssetKeyInput!]) {
    repositoriesOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on RepositoryConnection {
        nodes {
          __typename
          id
          ...RepositoryLiveFragment
        }
      }
    }
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      ...AssetNodeLiveFragment
    }
  }
  ${REPOSITORY_LIVE_FRAGMENT}
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

// Helpers

const isNodeOffscreen = (
  layoutNode: {x: number; y: number; width: number; height: number},
  bounds: {top: number; left: number; right: number; bottom: number},
) => {
  return (
    layoutNode.x + layoutNode.width < bounds.left ||
    layoutNode.y + layoutNode.height < bounds.top ||
    layoutNode.x > bounds.right ||
    layoutNode.y > bounds.bottom
  );
};

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

const buildGraphQueryItems = (nodes: AssetNode[]) => {
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

// This is similar to react-router's "<Redirect />" in that it immediately performs
// the action you rendered.
//
const RecenterGraph: React.FC<{
  viewportRef: React.MutableRefObject<SVGViewport | undefined>;
  x: number;
  y: number;
}> = ({viewportRef, x, y}) => {
  React.useEffect(() => {
    viewportRef.current?.smoothZoomToSVGCoords(x, y, viewportRef.current.state.scale);
  }, [viewportRef, x, y]);

  return <span />;
};
