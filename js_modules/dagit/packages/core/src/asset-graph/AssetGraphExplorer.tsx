import {Box, Checkbox, Mono, NonIdealState, SplitPanelContainer} from '@dagster-io/ui';
import {isEqual} from 'lodash';
import flatMap from 'lodash/flatMap';
import pickBy from 'lodash/pickBy';
import uniq from 'lodash/uniq';
import uniqBy from 'lodash/uniqBy';
import without from 'lodash/without';
import React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  QueryRefreshState,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {LaunchAssetExecutionButton} from '../assets/LaunchAssetExecutionButton';
import {AssetKey} from '../assets/types';
import {SVGViewport} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';
import {closestNodeInDirection, isNodeOffscreen} from '../graph/common';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {
  GraphExplorerOptions,
  OptionsOverlay,
  QueryOverlay,
  RightInfoPanel,
  RightInfoPanelContent,
} from '../pipelines/GraphExplorer';
import {
  EmptyDAGNotice,
  EntirelyFilteredDAGNotice,
  LargeDAGNotice,
  LoadingNotice,
} from '../pipelines/GraphNotices';
import {ExplorerPath, instanceAssetsExplorerPathToURL} from '../pipelines/PipelinePathUtils';
import {SidebarPipelineOrJobOverview} from '../pipelines/SidebarPipelineOrJobOverview';
import {useDidLaunchEvent} from '../runs/RunUtils';
import {PipelineSelector} from '../types/globalTypes';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {Loading} from '../ui/Loading';

import {AssetEdges} from './AssetEdges';
import {AssetNode, AssetNodeMinimal} from './AssetNode';
import {ForeignNode} from './ForeignNode';
import {OmittedAssetsNotice} from './OmittedAssetsNotice';
import {SidebarAssetInfo} from './SidebarAssetInfo';
import {
  GraphData,
  graphHasCycles,
  LiveData,
  GraphNode,
  isSourceAsset,
  tokenForAssetKey,
  displayNameForAssetKey,
} from './Utils';
import {AssetGraphLayout} from './layout';
import {AssetGraphQuery_assetNodes} from './types/AssetGraphQuery';
import {useAssetGraphData} from './useAssetGraphData';
import {useFindJobForAsset} from './useFindJobForAsset';
import {useLiveDataForAssetKeys} from './useLiveDataForAssetKeys';

type AssetNode = AssetGraphQuery_assetNodes;

interface Props {
  options: GraphExplorerOptions;
  setOptions?: (options: GraphExplorerOptions) => void;

  pipelineSelector?: PipelineSelector;
  filterNodes?: (assetNode: AssetGraphQuery_assetNodes) => boolean;

  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
}

const EXPERIMENTAL_MINI_SCALE = 0.5;

export const AssetGraphExplorer: React.FC<Props> = (props) => {
  const {
    fetchResult,
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    applyingEmptyDefault,
  } = useAssetGraphData(props.pipelineSelector, props.explorerPath.opsQuery, props.filterNodes);

  const {liveResult, liveDataByNode} = useLiveDataForAssetKeys(
    props.pipelineSelector,
    assetGraphData,
    graphAssetKeys,
  );

  const liveDataRefreshState = useQueryRefreshAtInterval(liveResult, FIFTEEN_SECONDS);

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
            key={props.explorerPath.pipelineName}
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

  const history = useHistory();
  const findJobForAsset = useFindJobForAsset();
  const {flagExperimentalAssetDAG: experiments} = useFeatureFlags();

  const selectedAssetValues = explorerPath.opNames[explorerPath.opNames.length - 1].split(',');
  const selectedGraphNodes = Object.values(assetGraphData.nodes).filter((node) =>
    selectedAssetValues.includes(tokenForAssetKey(node.definition.assetKey)),
  );
  const lastSelectedNode = selectedGraphNodes[selectedGraphNodes.length - 1];
  const launchGraphNodes = selectedGraphNodes.length
    ? selectedGraphNodes
    : Object.values(assetGraphData.nodes).filter((a) => !isSourceAsset(a.definition));

  const isGlobalGraph = !pipelineSelector;

  const onSelectNode = React.useCallback(
    async (
      e: React.MouseEvent<any> | React.KeyboardEvent<any>,
      assetKey: {path: string[]},
      node: GraphNode | null,
    ) => {
      e.stopPropagation();

      const token = tokenForAssetKey(assetKey);
      const nodeIsInDisplayedGraph = node?.definition;

      let clicked: {opNames: string[]; jobName: string | null} = {opNames: [], jobName: null};

      if (nodeIsInDisplayedGraph) {
        // The asset's defintion was provided in our job.assetNodes query. Show it in the current graph.
        clicked = {opNames: node.definition.opNames, jobName: explorerPath.pipelineName};
      } else {
        // The asset's definition was not provided in our query for job.assetNodes. It's either
        // in another job or asset group, or is a source asset not defined in any repository.
        clicked = await findJobForAsset(assetKey);
      }

      if (!clicked.opNames.length) {
        // This op has no definition in any loaded repository (source asset).
        // The best we can do is show the asset page. This will still be mostly empty,
        // but there can be a description.
        history.push(`/instance/assets/${assetKey.path.join('/')}?view=definition`);
        return;
      }

      if (!clicked.jobName && !isGlobalGraph) {
        // This asset has a definition (opName) but isn't in any non asset-group jobs.
        // We can switch to the instance-wide asset graph and see it in context there.
        history.push(
          instanceAssetsExplorerPathToURL({
            opsQuery: `++"${token}"++`,
            opNames: [token],
          }),
        );
        return;
      }

      // This asset is in different job (and we're in the job explorer),
      // go to the other job.
      if (!isGlobalGraph && clicked.jobName !== explorerPath.pipelineName) {
        onChangeExplorerPath(
          {...explorerPath, opNames: [token], opsQuery: '', pipelineName: clicked.jobName!},
          'replace',
        );
        return;
      }

      // This asset is in a job and we can stay in the job graph explorer!
      // If it's in our current job, allow shift / meta multi-selection.
      let nextOpsNameSelection = token;

      if (e.shiftKey || e.metaKey) {
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
          opsQuery: nodeIsInDisplayedGraph
            ? explorerPath.opsQuery
            : `${explorerPath.opsQuery},++"${token}"++`,
          pipelineName: explorerPath.pipelineName,
        },
        'replace',
      );
    },
    [
      isGlobalGraph,
      explorerPath,
      onChangeExplorerPath,
      findJobForAsset,
      history,
      lastSelectedNode,
      assetGraphData,
    ],
  );

  const {layout, loading, async} = useAssetLayout(assetGraphData);

  const viewportEl = React.useRef<SVGViewport>();

  const [lastRenderedLayout, setLastRenderedLayout] = React.useState<AssetGraphLayout | null>(null);
  const renderingNewLayout = lastRenderedLayout !== layout;

  React.useEffect(() => {
    if (!renderingNewLayout || !layout || !viewportEl.current) {
      return;
    }
    // The first render where we have our layout and viewport, autocenter or
    // focus on the selected node. (If selection was specified in the URL).
    // Don't animate this change.
    if (lastSelectedNode) {
      viewportEl.current.zoomToSVGBox(layout.nodes[lastSelectedNode.id].bounds, false);
      viewportEl.current.focus();
    } else {
      viewportEl.current.autocenter(false);
    }
    setLastRenderedLayout(layout);
  }, [renderingNewLayout, lastSelectedNode, layout, viewportEl]);

  const onClickBackground = () =>
    onChangeExplorerPath(
      {...explorerPath, pipelineName: explorerPath.pipelineName, opNames: []},
      'replace',
    );

  const onArrowKeyDown = (e: React.KeyboardEvent<any>, dir: string) => {
    if (!layout) {
      return;
    }
    const hasDefinition = (node: {id: string}) => !!assetGraphData.nodes[node.id]?.definition;
    const layoutWithoutExternalLinks = {...layout, nodes: pickBy(layout.nodes, hasDefinition)};

    const nextId = closestNodeInDirection(layoutWithoutExternalLinks, lastSelectedNode.id, dir);
    const node = nextId && assetGraphData.nodes[nextId];
    if (node && viewportEl.current) {
      onSelectNode(e, node.assetKey, node);
      viewportEl.current.zoomToSVGBox(layout.nodes[nextId].bounds, true);
    }
  };

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
          {loading || !layout ? (
            <LoadingNotice async={async} nodeType="asset" />
          ) : (
            <SVGViewport
              ref={(r) => (viewportEl.current = r || undefined)}
              interactor={SVGViewport.Interactors.PanAndZoom}
              graphWidth={layout.width}
              graphHeight={layout.height}
              onClick={onClickBackground}
              onArrowKeyDown={onArrowKeyDown}
              onDoubleClick={(e) => {
                viewportEl.current?.autocenter(true);
                e.stopPropagation();
              }}
              maxZoom={1.2}
              maxAutocenterZoom={1.0}
            >
              {({scale: _scale}, viewportRect) => (
                <SVGContainer width={layout.width} height={layout.height}>
                  <AssetEdges
                    edges={layout.edges}
                    extradark={experiments && _scale < EXPERIMENTAL_MINI_SCALE}
                  />

                  {Object.values(layout.bundles)
                    .sort((a, b) => a.id.length - b.id.length)
                    .map(({id, bounds}) => {
                      if (experiments && _scale < EXPERIMENTAL_MINI_SCALE) {
                        const path = JSON.parse(id);
                        return (
                          <foreignObject
                            x={bounds.x}
                            y={bounds.y}
                            width={bounds.width}
                            height={bounds.height + 10}
                            key={id}
                            onDoubleClick={(e) => {
                              viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                              e.stopPropagation();
                            }}
                          >
                            <AssetNodeMinimal
                              definition={{assetKey: {path}}}
                              selected={selectedGraphNodes.some((g) =>
                                hasPathPrefix(g.assetKey.path, path),
                              )}
                            />
                          </foreignObject>
                        );
                      }
                      return (
                        <foreignObject
                          x={bounds.x}
                          y={bounds.y}
                          width={bounds.width}
                          height={bounds.height + 10}
                          key={id}
                        >
                          <Mono
                            style={{
                              opacity:
                                _scale > EXPERIMENTAL_MINI_SCALE
                                  ? (_scale - EXPERIMENTAL_MINI_SCALE) / 0.2
                                  : 0,
                              fontWeight: 600,
                            }}
                          >
                            {displayNameForAssetKey({path: JSON.parse(id)})}
                          </Mono>
                          <div
                            style={{
                              inset: 0,
                              top: 24,
                              position: 'absolute',
                              borderRadius: 10,
                              border: `${3 / _scale}px dashed rgba(200,200,215,0.4)`,
                            }}
                          />
                        </foreignObject>
                      );
                    })}

                  {Object.values(layout.nodes).map(({id, bounds}, index) => {
                    const graphNode = assetGraphData.nodes[id];
                    const path = JSON.parse(id);
                    if (!renderingNewLayout && isNodeOffscreen(bounds, viewportRect)) {
                      return id === lastSelectedNode?.id ? (
                        <RecenterGraph
                          key={index}
                          viewportRef={viewportEl}
                          x={bounds.x + bounds.width / 2}
                          y={bounds.y + bounds.height / 2}
                        />
                      ) : null;
                    }

                    if (experiments && _scale < EXPERIMENTAL_MINI_SCALE) {
                      const isWithinBundle = Object.keys(layout.bundles).some((bundleId) =>
                        hasPathPrefix(path, JSON.parse(bundleId)),
                      );
                      if (isWithinBundle) {
                        return null;
                      }

                      return (
                        <foreignObject
                          {...bounds}
                          key={id}
                          onClick={(e) => onSelectNode(e, {path}, graphNode)}
                          onDoubleClick={(e) => {
                            viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                            e.stopPropagation();
                          }}
                        >
                          <AssetNodeMinimal
                            definition={graphNode.definition}
                            selected={selectedGraphNodes.includes(graphNode)}
                          />
                        </foreignObject>
                      );
                    }

                    return (
                      <foreignObject
                        {...bounds}
                        key={id}
                        onClick={(e) => onSelectNode(e, {path}, graphNode)}
                        onDoubleClick={(e) => {
                          viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                          e.stopPropagation();
                        }}
                        style={{overflow: 'visible'}}
                      >
                        {!graphNode || !graphNode.definition.opNames.length ? (
                          <ForeignNode assetKey={{path}} />
                        ) : (
                          <AssetNode
                            definition={graphNode.definition}
                            liveData={liveDataByNode[graphNode.id]}
                            selected={selectedGraphNodes.includes(graphNode)}
                          />
                        )}
                      </foreignObject>
                    );
                  })}
                </SVGContainer>
              )}
            </SVGViewport>
          )}
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
                        selectedGraphNodes.length && selectedGraphNodes[0].definition.opNames.length
                          ? selectedGraphNodes[0].definition.opNames
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

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;

// Helpers

const hasPathPrefix = (path: string[], prefix: string[]) => {
  return isEqual(prefix, path.slice(0, prefix.length));
};

const graphDirectionOf = ({
  graph,
  from,
  to,
}: {
  graph: GraphData;
  from: GraphNode;
  to: GraphNode;
}) => {
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
  {graph, from, to}: {graph: GraphData; from: GraphNode; to: GraphNode},
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

const titleForLaunch = (nodes: GraphNode[], liveDataByNode: LiveData) => {
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
    viewportRef.current?.zoomToSVGCoords(x, y, true);
  }, [viewportRef, x, y]);

  return <span />;
};
